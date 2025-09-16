import pyshark
import psutil
import socket

# Replace with your actual network interface name (Wi-Fi or Ethernet)
INTERFACE = r'\Device\NPF_{DF7B505F-FB0E-4D33-960A-77AA1D45174F}'

def get_process_name_by_port(port):
    """Return process name and PID using a local port"""
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == port:
            try:
                p = psutil.Process(conn.pid)
                return f"{p.name()} (PID {conn.pid})"
            except Exception:
                return f"PID {conn.pid}"
    return "Unknown"

print("=== TLS SNI Sniffer Started ===")
print("Press Ctrl+C to stop...\n")

capture = pyshark.LiveCapture(interface=INTERFACE, bpf_filter='tcp port 443')

try:
    for packet in capture.sniff_continuously():
        # Check if this is a TLS handshake
        if 'tls' in packet and hasattr(packet.tls, 'handshake_extensions_server_name'):
            sni = packet.tls.handshake_extensions_server_name
            # Local port to map PID
            try:
                local_port = int(packet.tcp.srcport)
            except:
                local_port = None
            process = get_process_name_by_port(local_port) if local_port else "Unknown"
            remote_ip = packet.ip.dst if hasattr(packet, 'ip') else packet.ipv6.dst
            remote_port = packet.tcp.dstport
            print(f"[{process}] → {sni} ({remote_ip}:{remote_port})")
except KeyboardInterrupt:
    print("\nSniffer stopped.")
except Exception as e:
    print(f"Error: {e}")

