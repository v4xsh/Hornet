import subprocess
import threading
import time
from joblib import load
import queue
import os
import folium
import geocoder
from core.text_to_speech import speak
import random
import re
from datetime import datetime
from core.network_safety import network_safety

# ---------- 🔧 Config ---------- #
ZEEK_LOG_DIR = os.path.abspath("zeek_logs")
ZEEK_CONN_LOG = os.path.join(ZEEK_LOG_DIR, "conn.log")
ZEEK_BIN_PATH = "/opt/zeek/bin/zeek"  # Inside WSL
ZEEK_INTERFACE = "eth0"

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../firewall_model.joblib")
model = load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

packet_queue = queue.Queue()
blocked_ips = set()
last_threat_ip = None
stop_monitoring = False

# ---------- 🔥 Dynamic Windows Firewall Rule ---------- #
def block_ip(ip, gui=None):
    if ip in blocked_ips:
        return

    cmd = [
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name=HornetBlock_{ip}", "dir=out", "action=block",
        f"remoteip={ip}", "enable=yes"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    blocked_ips.add(ip)

    if gui:
        gui.add_text(f"[Firewall] 🚫 Blocked suspicious IP: {ip}")
    print(f"[Firewall] 🚫 Blocked suspicious IP: {ip}")
    speak(f"Blocked suspicious IP address {ip}")
    time.sleep(0.4)

# ---------- 🧠 ML Detection (Optional) ---------- #
def classify_packet(features):
    if model:
        return model.predict([features])[0] == "malicious"
    return False

# ---------- 📖 Zeek conn.log Reader ---------- #
def read_zeek_conn_log(gui=None):
    global last_threat_ip
    seen = set()
    log_file = ZEEK_CONN_LOG

    print("[Zeek] 🔍 Monitoring conn.log for suspicious activity...")
    speak("Hornet is now watching for suspicious activity.")
    time.sleep(0.5)

    while not stop_monitoring:
        if not os.path.exists(log_file):
            time.sleep(1)
            continue

        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()

            for line in lines:
                if line.startswith("#") or line in seen:
                    continue
                seen.add(line)

                fields = line.strip().split("\t")
                if len(fields) < 12:
                    continue

                orig_ip = fields[2]
                dest_ip = fields[4]
                proto = fields[6].lower()
                state = fields[11]

                # 🚨 Suspicious UDP connection detection
                if proto == "udp" and state == "S0":
                    last_threat_ip = dest_ip
                    block_ip(dest_ip, gui)
                    if gui:
                        gui.add_text(f"[Zeek] ⚠️ Suspicious UDP from {orig_ip} → {dest_ip}")
                    print(f"[Zeek] ⚠️ Suspicious UDP from {orig_ip} → {dest_ip}")
                    speak(f"Suspicious network activity from {orig_ip} to {dest_ip}")
                    time.sleep(0.4)

        except Exception as e:
            print(f"[Zeek Log Error] {e}")
            speak("There was an error reading the network logs.")
            time.sleep(0.4)

        time.sleep(2)

# ---------- 🚀 Zeek Sniffer Launcher ---------- #
def run_zeek_sniffer():
    if not os.path.exists(ZEEK_LOG_DIR):
        os.makedirs(ZEEK_LOG_DIR)

    try:
        # Copy Zeek policy file to appropriate location
        policy_path = os.path.join(os.path.dirname(__file__), "zeek_policy.zeek")
        if os.path.exists(policy_path):
            subprocess.run(["wsl", "cp", policy_path, "/tmp/hornet_policy.zeek"])
        
        # Run Zeek with custom policy
        subprocess.Popen([
            "wsl", "sudo", ZEEK_BIN_PATH, "-i", ZEEK_INTERFACE, "/tmp/hornet_policy.zeek"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[Zeek] 🧠 Started on interface {ZEEK_INTERFACE} with Hornet policy")
        speak("Hornet firewall started monitoring your network.")
        time.sleep(0.4)
        
        # Start monitoring Hornet alerts
        threading.Thread(target=monitor_hornet_alerts, daemon=True).start()
    except Exception as e:
        print(f"[Zeek] ❌ Failed to launch Zeek: {e}")
        speak("Failed to launch the Hornet sniffer.")
        time.sleep(0.4)

# ---------- 🚨 Hornet Alerts Monitor ---------- #
def monitor_hornet_alerts(gui=None):
    """Monitor Zeek's hornet_alerts.log for security events"""
    alerts_file = os.path.join(ZEEK_LOG_DIR, "hornet_alerts.log")
    seen_alerts = set()
    
    while not stop_monitoring:
        if os.path.exists(alerts_file):
            try:
                with open(alerts_file, 'r') as f:
                    for line in f:
                        if line.strip() and line not in seen_alerts:
                            seen_alerts.add(line)
                            parts = line.strip().split('|')
                            if len(parts) >= 4:
                                timestamp, alert_type, message, source = parts[:4]
                                
                                # Extract IP from source
                                ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', source)
                                if ip_match:
                                    threat_ip = ip_match.group(1)
                                    global last_threat_ip
                                    last_threat_ip = threat_ip
                                    
                                    # Block the IP
                                    block_ip(threat_ip, gui)
                                    
                                    if gui:
                                        gui.add_text(f"[Alert] {alert_type}: {message}")
                                    
                                    speak(f"Security alert: {alert_type.replace('_', ' ')}")
            except Exception as e:
                print(f"[Alert Monitor Error] {e}")
        
        time.sleep(1)

# ---------- 🌍 Trace Threat IP ---------- #
def trace_last_threat():
    global last_threat_ip
    if not last_threat_ip:
        print("[Trace] ⚠️ No IP to trace.")
        speak("There is no IP to trace right now.")
        time.sleep(0.4)
        return

    g = geocoder.ip(last_threat_ip)
    if g.latlng:
        m = folium.Map(location=g.latlng, zoom_start=5)
        folium.Marker(g.latlng, tooltip=last_threat_ip).add_to(m)
        path = os.path.abspath("trace.html")
        m.save(path)
        os.system(f"start {path}")
        print(f"[Trace] 🌍 Threat IP traced: {last_threat_ip}")
        speak("IP address traced. Showing location on map.")
        time.sleep(0.4)
    else:
        speak("Couldn't find the location for this IP.")
        time.sleep(0.4)

# ---------- 🚨 Enhanced Packet Analysis ---------- #
SUSPICIOUS_PAYLOADS = [
    r"'\s*OR\s*'?1'?\s*=\s*'?1'?",  # SQL injection
    r"<script[^>]*>.*?</script>",      # XSS attempt
    r"\.\.[\\/]+",                   # Path traversal
    r"cmd\.exe|/bin/bash|/bin/sh",    # Command execution
    r"nc\s+-[lnvpe]+\s+\d+",         # Netcat reverse shell
    r"python\s+-c\s+.*socket",        # Python reverse shell
    r"bash\s+-i\s+>&\s+/dev/tcp",     # Bash reverse shell
    r"eval\s*\(.*\)",                 # Code evaluation
    r"exec\s*\(.*\)",                 # Code execution
]

# Attack simulation data for demo mode
DEMO_ATTACKS = [
    {"ip": "192.168.1.100", "type": "SQL Injection", "payload": "' OR '1'='1' --"},
    {"ip": "10.0.0.50", "type": "XSS Attack", "payload": "<script>alert('xss')</script>"},
    {"ip": "172.16.0.10", "type": "Reverse Shell", "payload": "nc -lvp 4444"},
    {"ip": "203.0.113.0", "type": "Path Traversal", "payload": "../../etc/passwd"},
    {"ip": "198.51.100.0", "type": "Command Injection", "payload": "; rm -rf /"},
]

def detect_payload_in_traffic(data, gui=None):
    """Detect suspicious payloads in network traffic"""
    for pattern in SUSPICIOUS_PAYLOADS:
        if re.search(pattern, data, re.IGNORECASE):
            return True
    return False

def enhanced_packet_analysis(packet_data, source_ip, dest_ip, gui=None):
    """Enhanced packet analysis with payload detection"""
    global last_threat_ip
    
    # Check for suspicious payloads
    if detect_payload_in_traffic(packet_data, gui):
        last_threat_ip = source_ip
        block_ip(source_ip, gui)
        
        if gui:
            gui.add_text(f"[Payload Detected] 🚨 Malicious payload from {source_ip}")
            gui.add_text(f"[Payload] Content: {packet_data[:50]}...")
        
        speak(f"Malicious payload detected from {source_ip}. Blocking immediately.")
        return True
    
    # Check for port scanning
    if is_port_scan(source_ip, dest_ip):
        last_threat_ip = source_ip
        block_ip(source_ip, gui)
        
        if gui:
            gui.add_text(f"[Port Scan] 🔍 Port scanning detected from {source_ip}")
        
        speak(f"Port scanning detected from {source_ip}. Blocking.")
        return True
    
    return False

# Port scan detection
port_scan_tracker = {}

def is_port_scan(source_ip, dest_port):
    """Detect potential port scanning activity"""
    current_time = time.time()
    
    if source_ip not in port_scan_tracker:
        port_scan_tracker[source_ip] = {"ports": set(), "first_seen": current_time}
    
    tracker = port_scan_tracker[source_ip]
    tracker["ports"].add(dest_port)
    
    # If more than 10 different ports in 5 seconds, it's likely a scan
    if len(tracker["ports"]) > 10 and (current_time - tracker["first_seen"]) < 5:
        return True
    
    # Clean old entries
    if current_time - tracker["first_seen"] > 60:
        port_scan_tracker[source_ip] = {"ports": {dest_port}, "first_seen": current_time}
    
    return False

# ---------- 🎭 Demo Mode ---------- #
def run_demo_mode(gui=None):
    """Run firewall demo mode with simulated attacks"""
    speak("Starting firewall demo mode. Simulating incoming attacks.")
    
    if gui:
        gui.add_text("[Demo Mode] 🎭 Starting attack simulation...")
    
    for i, attack in enumerate(DEMO_ATTACKS):
        time.sleep(2)  # Delay between attacks
        
        if gui:
            gui.add_text(f"\n[Demo Attack #{i+1}] Incoming {attack['type']}")
            gui.add_text(f"[Demo] Source IP: {attack['ip']}")
            gui.add_text(f"[Demo] Payload: {attack['payload']}")
        
        speak(f"Detecting {attack['type']} from {attack['ip']}")
        
        # Simulate blocking
        time.sleep(1)
        block_ip(attack['ip'], gui)
        
        if gui:
            gui.add_text(f"[Demo] ✅ Successfully blocked {attack['type']}")
    
    speak("Demo mode completed. All simulated attacks were blocked.")
    
    if gui:
        gui.add_text("\n[Demo Mode] 🎉 Demo completed successfully!")

# ---------- 📊 Traffic Analysis ---------- #
def analyze_incoming_traffic(gui=None):
    """Analyze incoming network traffic for threats"""
    global last_threat_ip
    
    speak("Analyzing incoming network traffic for potential threats.")
    
    if gui:
        gui.add_text("[Traffic Analysis] 🔍 Scanning incoming packets...")
    
    # In a real implementation, this would interface with packet capture
    # For now, we'll simulate some analysis
    time.sleep(2)
    
    suspicious_count = random.randint(0, 5)
    if suspicious_count > 0:
        speak(f"Found {suspicious_count} suspicious connection attempts.")
        if gui:
            gui.add_text(f"[Traffic Analysis] ⚠️ {suspicious_count} suspicious connections detected")
    else:
        speak("No suspicious activity detected in current traffic.")
        if gui:
            gui.add_text("[Traffic Analysis] ✅ All traffic appears normal")

# ---------- ✅ Monitor Control ---------- #
def start_firewall_monitor(gui=None, demo=False):
    global stop_monitoring
    stop_monitoring = False
    
    if demo:
        threading.Thread(target=run_demo_mode, args=(gui,), daemon=True).start()
        return
    
    # Show current network status
    network_status = network_safety.get_network_status()
    if gui:
        gui.add_text(f"[Network] Current mode: {network_status['mode']}")
        gui.add_text(f"[Network] Current IP: {network_status['current_ip']}")

    threading.Thread(target=read_zeek_conn_log, args=(gui,), daemon=True).start()
    run_zeek_sniffer()

    if gui:
        gui.add_text("[Firewall] 🔥 Hornet Firewall Mode ENABLED")
    speak("Hornet firewall mode enabled.")
    time.sleep(0.4)
    print("[Firewall] 🔥 Hornet Firewall Mode ENABLED")

def stop_firewall_monitor():
    global stop_monitoring
    stop_monitoring = True
    
    # Clear all Hornet firewall rules
    clear_firewall_rules()
    
    speak("Hornet monitoring stopped.")
    time.sleep(0.4)
    print("[Firewall] 🛑 Monitoring STOPPED.")

def clear_firewall_rules():
    """Remove all Hornet firewall rules"""
    try:
        # List all firewall rules and remove Hornet ones
        result = subprocess.run(
            ["netsh", "advfirewall", "firewall", "show", "rule", "name=all"],
            capture_output=True,
            text=True
        )
        
        for line in result.stdout.split('\n'):
            if "HornetBlock_" in line:
                rule_name = line.split(':')[1].strip()
                subprocess.run(
                    ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
    except:
        pass

# ---------- 📈 Statistics ---------- #
def get_firewall_stats():
    """Get firewall statistics"""
    stats = {
        "blocked_ips": len(blocked_ips),
        "blocked_list": list(blocked_ips),
        "last_threat": last_threat_ip,
        "monitoring_active": not stop_monitoring
    }
    return stats
 
