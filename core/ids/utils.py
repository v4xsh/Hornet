import platform, time, hashlib

def now_ms() -> int:
    return int(time.time() * 1000)

def os_family() -> str:
    sysname = platform.system().lower()
    if "windows" in sysname: return "win"
    if "linux" in sysname: return "linux"
    return "other"

def hash_endpoint(ip: str, port: int) -> str:
    return hashlib.sha1(f"{ip}:{port}".encode()).hexdigest()[:10]

