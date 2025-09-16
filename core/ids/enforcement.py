import subprocess, platform, os, ctypes, psutil
from ..logging_ids import get_ids_logger
from ..config_ids import IDSConfig

log = get_ids_logger("hornet.ids.enforce")


class Enforcement:
    def __init__(self, cfg: IDSConfig):
        self.cfg = cfg
        self._family = cfg.platform if cfg.platform != "auto" else _os_family()

    def apply(self, decision, flow):
        # Analyze behavior
        behavior_summary = self._analyze_behavior(flow)

        # Camera/mic activity
        cam_mic_behavior = []
        if flow.get("cam_active"):
            cam_mic_behavior.append("Accessing camera")
        if flow.get("mic_active"):
            cam_mic_behavior.append("Accessing microphone")
        if cam_mic_behavior:
            behavior_summary += "; " + "; ".join(cam_mic_behavior)

        # Log message with host info
        msg = (
            "⚠️ Activity Detected\n"
            f"Process: {flow['proc']}\n"
            f"Target: {flow.get('r_host', flow['r_ip'])} ({flow['r_ip']}:{flow['r_port']})\n"
            f"Direction: outbound\n"
            f"Behavior: {behavior_summary}\n"
            f"Risk Score: {decision['risk']:.2f}\n"
        )
        log.info(msg)

        # Block if required
        if decision["level"] == "block" and not self.cfg.dry_run:
            if not _check_admin(self._family):
                log.error("Blocking requires admin/root privileges. Restart as Administrator/root.")
                return
            self._block(flow['r_ip'])

    def _analyze_behavior(self, flow):
        behaviors = []
        try:
            p = psutil.Process(flow["pid"])
            exe_path = p.exe() or ""
            exe_base = os.path.basename(exe_path) if exe_path else flow.get("proc", "unknown")
            behaviors.append(f"Running {exe_base}")
            try:
                if p.connections(kind="inet"):
                    behaviors.append("Connecting to external servers")
            except psutil.AccessDenied:
                pass
        except psutil.NoSuchProcess:
            return f"Process {flow.get('proc', 'unknown')} (PID: {flow['pid']}) no longer exists"
        except Exception:
            return "Performing unknown actions"
        return "; ".join(behaviors)

    def _block(self, ip: str):
        if self._family == "win":
            cmd = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                f'New-NetFirewallRule -DisplayName "HornetBlock_{ip}" -Direction Outbound -RemoteAddress {ip} -Action Block -Profile Any'
            ]
        elif self._family == "linux":
            cmd = ["iptables", "-I", "OUTPUT", "-d", ip, "-j", "DROP"]
        else:
            log.error("Unsupported OS for blocking action")
            return
        try:
            subprocess.run(cmd, check=True, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            log.warning(f"[ENFORCED] Blocked outbound connection to {ip}")
        except Exception as e:
            log.exception(f"Failed to block {ip}: {e}")


def _os_family():
    s = platform.system().lower()
    if "windows" in s: return "win"
    if "linux" in s: return "linux"
    return "other"


def _check_admin(family: str) -> bool:
    try:
        if family == "linux":
            return os.geteuid() == 0
        elif family == "win":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return False
    except Exception:
        return False

