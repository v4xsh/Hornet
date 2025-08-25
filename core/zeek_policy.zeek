@load base/frameworks/notice
@load base/protocols/conn
@load base/protocols/http
@load base/protocols/dns
@load base/protocols/ssh

module HornetFirewall;

export {
    redef enum Notice::Type += {
        Suspicious_Payload,
        Port_Scan_Detected,
        Reverse_Shell_Attempt,
        SQL_Injection_Attempt,
        XSS_Attack_Attempt,
        Excessive_Failed_SSH,
        DNS_Tunneling_Suspect
    };
    
    # Configuration
    const suspicious_payloads = /('.*OR.*'1'.*=.*'1'|<script.*>.*<\/script>|\.\.\/|cmd\.exe|\/bin\/bash|nc\s+-[lnvpe]+\s+\d+|python\s+-c.*socket|eval\s*\(|exec\s*\()/ &redef;
    
    const port_scan_threshold = 10 &redef;
    const port_scan_interval = 5 secs &redef;
    
    # Track port scanning
    global scan_tracker: table[addr] of set[port] &create_expire=60secs;
    global scan_first_seen: table[addr] of time &create_expire=60secs;
}

# Connection state tracking
event connection_state_remove(c: connection)
{
    local orig = c$id$orig_h;
    
    # Check for suspicious UDP connections
    if ( c$conn$proto == udp && c$conn$conn_state == "S0" )
    {
        NOTICE([$note=Suspicious_Payload,
                $msg=fmt("Suspicious UDP connection from %s to %s", orig, c$id$resp_h),
                $conn=c,
                $identifier=cat(orig)]);
    }
    
    # Port scan detection
    if ( orig !in scan_tracker )
    {
        scan_tracker[orig] = set();
        scan_first_seen[orig] = network_time();
    }
    
    add scan_tracker[orig][c$id$resp_p];
    
    if ( |scan_tracker[orig]| > port_scan_threshold && 
         network_time() - scan_first_seen[orig] < port_scan_interval )
    {
        NOTICE([$note=Port_Scan_Detected,
                $msg=fmt("Port scan detected from %s", orig),
                $conn=c,
                $identifier=cat(orig)]);
        
        # Reset tracking
        delete scan_tracker[orig];
        delete scan_first_seen[orig];
    }
}

# HTTP payload inspection
event http_request(c: connection, method: string, original_URI: string,
                   unescaped_URI: string, version: string)
{
    # Check for SQL injection attempts
    if ( /('.*OR.*'1'.*=.*'1'|SELECT.*FROM|DROP.*TABLE|INSERT.*INTO|UPDATE.*SET|DELETE.*FROM)/i in unescaped_URI )
    {
        NOTICE([$note=SQL_Injection_Attempt,
                $msg=fmt("SQL injection attempt from %s: %s", c$id$orig_h, unescaped_URI),
                $conn=c,
                $identifier=cat(c$id$orig_h)]);
    }
    
    # Check for XSS attempts
    if ( /<script.*>.*<\/script>|javascript:|onerror=|onload=/i in unescaped_URI )
    {
        NOTICE([$note=XSS_Attack_Attempt,
                $msg=fmt("XSS attack attempt from %s: %s", c$id$orig_h, unescaped_URI),
                $conn=c,
                $identifier=cat(c$id$orig_h)]);
    }
    
    # Check for command injection
    if ( /;.*\s*(cat|ls|rm|wget|curl|nc|bash|sh)\s+/i in unescaped_URI )
    {
        NOTICE([$note=Reverse_Shell_Attempt,
                $msg=fmt("Command injection attempt from %s: %s", c$id$orig_h, unescaped_URI),
                $conn=c,
                $identifier=cat(c$id$orig_h)]);
    }
}

# SSH brute force detection
global ssh_failures: table[addr] of count &create_expire=5mins &default=0;

event ssh_auth_failed(c: connection)
{
    local orig = c$id$orig_h;
    ssh_failures[orig] += 1;
    
    if ( ssh_failures[orig] > 5 )
    {
        NOTICE([$note=Excessive_Failed_SSH,
                $msg=fmt("SSH brute force attempt from %s", orig),
                $conn=c,
                $identifier=cat(orig)]);
        
        delete ssh_failures[orig];
    }
}

# DNS tunneling detection
event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
{
    # Check for unusually long DNS queries (potential tunneling)
    if ( |query| > 50 )
    {
        NOTICE([$note=DNS_Tunneling_Suspect,
                $msg=fmt("Potential DNS tunneling from %s: %s", c$id$orig_h, query),
                $conn=c,
                $identifier=cat(c$id$orig_h)]);
    }
    
    # Check for high entropy domains (randomized)
    local dots = 0;
    for ( i in query )
    {
        if ( query[i] == "." )
            dots += 1;
    }
    
    if ( dots > 4 )  # Excessive subdomains
    {
        NOTICE([$note=DNS_Tunneling_Suspect,
                $msg=fmt("Suspicious DNS query structure from %s: %s", c$id$orig_h, query),
                $conn=c,
                $identifier=cat(c$id$orig_h)]);
    }
}

# TCP payload inspection for reverse shells
event tcp_packet(c: connection, is_orig: bool, flags: string, seq: count, ack: count, len: count, payload: string)
{
    if ( len > 0 && suspicious_payloads in payload )
    {
        NOTICE([$note=Reverse_Shell_Attempt,
                $msg=fmt("Reverse shell pattern detected from %s", c$id$orig_h),
                $conn=c,
                $identifier=cat(c$id$orig_h)]);
    }
}

# Log all notices to a separate file for Hornet
event Notice::log_notice(rec: Notice::Info)
{
    if ( rec$note == Suspicious_Payload ||
         rec$note == Port_Scan_Detected ||
         rec$note == Reverse_Shell_Attempt ||
         rec$note == SQL_Injection_Attempt ||
         rec$note == XSS_Attack_Attempt ||
         rec$note == Excessive_Failed_SSH ||
         rec$note == DNS_Tunneling_Suspect )
    {
        # Write to hornet_alerts.log
        local f = open_for_append("hornet_alerts.log");
        print f, fmt("%s|%s|%s|%s", rec$ts, rec$note, rec$msg, rec$src);
        close(f);
    }
}
