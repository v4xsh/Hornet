from typing import List, Dict, Any
import psutil, time, socket, os, subprocess, json
from ..logging_ids import get_ids_logger

log = get_ids_logger("hornet.ids.features")

class FeatureExtractor:
    def __init__(self):
        self._proc_cache = {}
        self._cam_pids = set()
        self._mic_pids = set()
        self._update_cam_mic_pids()

    def _update_cam_mic_pids(self):
        """Query registry via PowerShell to get PIDs actively using camera/mic."""
        for device in ["webcam", "microphone"]:
            try:
                # This PowerShell script uses the exact logic from your working manual test.
                ps_script = f"""
$base = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\{device}\\NonPackaged'

Get-ChildItem -Path $base -ErrorAction SilentlyContinue | ForEach-Object {{
    # This is the same logic you confirmed works:
    $props = Get-ItemProperty -Path $_.PSPath
    $startTime = [datetime]::FromFileTime($props.LastUsedTimeStart)
    $stopTime = [datetime]::FromFileTime($props.LastUsedTimeStop)

    if ($stopTime -lt $startTime) {{
        $standardPath = $_.PSChildName.Replace('#', '\\')
        $procName = [System.IO.Path]::GetFileNameWithoutExtension($standardPath)
        
        # This is the only change: instead of Write-Host, we get the PID for Python.
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
                    if isinstance(data, int): pids = [data]
                    elif isinstance(data, list): pids = data
                
                if device == "webcam": self._cam_pids = set(pids)
                else: self._mic_pids = set(pids)

            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            except Exception as e:
                log.error(f"An unexpected error occurred while checking {device} usage: {e}")

    def _proc_name(self, pid: int) -> str:
        if pid in self._proc_cache:
            return self._proc_cache[pid]
        try:
            p = psutil.Process(pid)
            name = os.path.basename(p.name()).lower()
            self._proc_cache[pid] = name
            return name
        except psutil.NoSuchProcess:
            if pid in self._proc_cache:
                del self._proc_cache[pid]
            return "unknown"
        except Exception:
            return "unknown"

    def sample_flows(self) -> List[Dict[str, Any]]:
        self._update_cam_mic_pids()
        ts = time.time()
        results = []
        try:
            for c in psutil.net_connections(kind="inet"):
                if not (c.raddr and c.laddr and c.pid):
                    continue

                pid = c.pid
                item = {
                    "ts": ts, "pid": pid, "proc": self._proc_name(pid), "status": c.status,
                    "l_ip": c.laddr.ip, "l_port": c.laddr.port,
                    "r_ip": c.raddr.ip, "r_port": c.raddr.port,
                    "direction": "outbound",
                    "is_private_dst": _is_private_ip(c.raddr.ip),
                    "cam_active": pid in self._cam_pids,
                    "mic_active": pid in self._mic_pids,
                }
                results.append(item)
        except psutil.AccessDenied:
            log.warning("Access denied when sampling network connections. Run as admin for full visibility.")
        return results

def _is_private_ip(ip: str) -> bool:
    if ip.startswith(('10.', '192.168.')): return True
    if ip.startswith('172.'):
        try:
            second_octet = int(ip.split('.')[1])
            if 16 <= second_octet <= 31: return True
        except (IndexError, ValueError): return False
    return False