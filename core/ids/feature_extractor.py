import psutil, time, socket, os, json, requests, subprocess, threading, asyncio
from typing import List, Dict, Any
import pyshark

# Logger placeholder
import logging
log = logging.getLogger("hornet.ids.features")

# Replace this with your actual network interface
INTERFACE = r'\Device\NPF_{DF7B505F-FB0E-4D33-960A-77AA1D45174F}'


def _is_private_ip(ip: str) -> bool:
    if ip.startswith(('10.', '192.168.')):
        return True
    if ip.startswith('172.'):
        try:
            second_octet = int(ip.split('.')[1])
            if 16 <= second_octet <= 31:
                return True
        except (IndexError, ValueError):
            return False
    return False


class FeatureExtractor:
    def __init__(self):
        self._proc_cache = {}
        self._host_cache = {}
        self._cam_pids = set()
        self._mic_pids = set()
        self._update_cam_mic_pids()

        # TLS buffer
        self._tls_buffer = []
        self._tls_lock = threading.Lock()

        # Start TLS sniffer thread
        self._tls_thread = threading.Thread(target=self._tls_sniffer, daemon=True)
        self._tls_thread.start()

    def _update_cam_mic_pids(self):
        """Update camera/mic active PIDs using Windows registry."""
        for device in ["webcam", "microphone"]:
            try:
                ps_script = f"""
$base = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\{device}\\NonPackaged'
Get-ChildItem -Path $base -ErrorAction SilentlyContinue | ForEach-Object {{
    $props = Get-ItemProperty -Path $_.PSPath
    $startTime = [datetime]::FromFileTime($props.LastUsedTimeStart)
    $stopTime = [datetime]::FromFileTime($props.LastUsedTimeStop)
    if ($stopTime -lt $startTime) {{
        $standardPath = $_.PSChildName.Replace('#', '\\')
        $procName = [System.IO.Path]::GetFileNameWithoutExtension($standardPath)
        $procs = Get-Process -Name $procName -ErrorAction SilentlyContinue
        foreach ($p in $procs) {{ $p.Id }}
    }}
}} | ConvertTo-Json -Compress
"""
                out = subprocess.check_output(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                    stderr=subprocess.PIPE, shell=False
                )
                txt = out.decode('utf-8-sig', errors='ignore').strip()
                pids = []
                if txt and txt != "null":
                    data = json.loads(txt)
                    if isinstance(data, int):
                        pids = [data]
                    elif isinstance(data, list):
                        pids = data
                if device == "webcam":
                    self._cam_pids = set(pids)
                else:
                    self._mic_pids = set(pids)
            except Exception as e:
                log.error(f"Error checking {device}: {e}")

    def _proc_name(self, pid: int) -> str:
        if pid in self._proc_cache:
            return self._proc_cache[pid]
        try:
            p = psutil.Process(pid)
            name = os.path.basename(p.name()).lower()
            self._proc_cache[pid] = name
            return name
        except psutil.NoSuchProcess:
            self._proc_cache.pop(pid, None)
            return "unknown"
        except Exception:
            return "unknown"

    def _resolve_host(self, ip: str) -> str:
        if ip in self._host_cache:
            return self._host_cache[ip]
        try:
            host = socket.gethostbyaddr(ip)[0]
            if host != ip:
                self._host_cache[ip] = host
                return host
        except Exception:
            pass
        try:
            r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=1).json()
            host = r.get("hostname") or r.get("org") or ip
            self._host_cache[ip] = host
            return host
        except Exception:
            self._host_cache[ip] = ip
            return ip

    def _get_all_child_pids(self, pid: int) -> List[int]:
        try:
            p = psutil.Process(pid)
            children = p.children(recursive=True)
            return [p.pid] + [c.pid for c in children]
        except Exception:
            return [pid]

    def _pid_from_port(self, port: int) -> int:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port and conn.pid:
                return conn.pid
        return -1

    def _tls_sniffer(self):
        """Background TLS SNI sniffer (stores results in buffer)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        capture = pyshark.LiveCapture(interface=INTERFACE, bpf_filter='tcp port 443')
        for packet in capture.sniff_continuously():
            try:
                if 'tls' in packet and hasattr(packet.tls, 'handshake_extensions_server_name'):
                    sni = packet.tls.handshake_extensions_server_name
                    local_ip = getattr(packet, 'ip', {}).get('src', '0.0.0.0') if hasattr(packet, 'ip') else '0.0.0.0'
                    local_port = int(packet.tcp.srcport)
                    remote_ip = getattr(packet, 'ip', {}).get('dst', '0.0.0.0') if hasattr(packet, 'ip') else '0.0.0.0'
                    with self._tls_lock:
                        self._tls_buffer.append({
                            "ts": time.time(),
                            "pid": self._pid_from_port(local_port),
                            "proc": self._proc_name(self._pid_from_port(local_port)),
                            "l_ip": local_ip,
                            "l_port": local_port,
                            "r_ip": remote_ip,
                            "r_port": int(packet.tcp.dstport),
                            "r_host": sni,
                            "service": sni.split('.')[-2] if '.' in sni else sni,
                            "direction": "outbound",
                            "is_private_dst": _is_private_ip(remote_ip),
                            "cam_active": False,
                            "mic_active": False,
                            "source": "tls_sni"
                        })
            except Exception as e:
                log.debug(f"SNI parse error: {e}")

    def sample_flows(self) -> List[Dict[str, Any]]:
        flows = []
        self._update_cam_mic_pids()
        ts = time.time()

        try:
            for c in psutil.net_connections(kind="inet"):
                if not (c.raddr and c.laddr and c.pid):
                    continue
                for pid in self._get_all_child_pids(c.pid):
                    r_ip = c.raddr.ip
                    r_host = self._resolve_host(r_ip)
                    flows.append({
                        "ts": ts,
                        "pid": pid,
                        "proc": self._proc_name(pid),
                        "status": c.status,
                        "l_ip": c.laddr.ip,
                        "l_port": c.laddr.port,
                        "r_ip": r_ip,
                        "r_port": c.raddr.port,
                        "r_host": r_host,
                        "service": r_host.split('.')[-2] if r_host and '.' in r_host else r_host,
                        "direction": "outbound",
                        "is_private_dst": _is_private_ip(r_ip),
                        "cam_active": pid in self._cam_pids,
                        "mic_active": pid in self._mic_pids,
                        "source": "psutil"
                    })
        except psutil.AccessDenied:
            log.warning("Access denied when sampling network connections. Run as admin for full visibility.")

        with self._tls_lock:
            flows.extend(self._tls_buffer)
            self._tls_buffer.clear()

        return flows
