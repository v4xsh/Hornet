import os
import subprocess
import zipfile
import requests
import tempfile
import shutil
from pathlib import Path

def download_tor_windows():
    """Download and install TOR for Windows"""
    try:
        print("[TOR Install] Downloading TOR for Windows...")
        
        # TOR download URL (stable version)
        tor_url = "https://archive.torproject.org/tor-package-archive/torbrowser/12.5.6/tor-expert-bundle-windows-x86_64-12.5.6.tar.gz"
        
        # Create tor directory
        tor_dir = os.path.join(os.path.dirname(__file__), "tor")
        os.makedirs(tor_dir, exist_ok=True)
        
        # Download TOR
        with tempfile.TemporaryDirectory() as temp_dir:
            tor_archive = os.path.join(temp_dir, "tor.tar.gz")
            
            response = requests.get(tor_url, stream=True)
            response.raise_for_status()
            
            with open(tor_archive, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("[TOR Install] Extracting TOR...")
            
            # Extract using Python's tarfile
            import tarfile
            with tarfile.open(tor_archive, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # Find and copy tor.exe
            for root, dirs, files in os.walk(temp_dir):
                if 'tor.exe' in files:
                    src_tor = os.path.join(root, 'tor.exe')
                    dst_tor = os.path.join(tor_dir, 'tor.exe')
                    shutil.copy2(src_tor, dst_tor)
                    print(f"[TOR Install] TOR installed to: {dst_tor}")
                    
                    # Make executable (on Unix systems)
                    if os.name != 'nt':
                        os.chmod(dst_tor, 0o755)
                    
                    return dst_tor
        
        print("[TOR Install] TOR installation failed - tor.exe not found in archive")
        return None
        
    except Exception as e:
        print(f"[TOR Install] Error downloading TOR: {e}")
        return None

def install_tor_via_choco():
    """Try to install TOR via Chocolatey"""
    try:
        print("[TOR Install] Attempting to install TOR via Chocolatey...")
        result = subprocess.run(
            ["choco", "install", "tor", "-y"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print("[TOR Install] TOR installed successfully via Chocolatey")
            return True
        else:
            print(f"[TOR Install] Chocolatey installation failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("[TOR Install] Chocolatey not found")
        return False
    except Exception as e:
        print(f"[TOR Install] Chocolatey installation error: {e}")
        return False

def find_system_tor():
    """Find TOR installation on the system"""
    possible_paths = [
        r"C:\Program Files\Tor Browser\Browser\TorBrowser\Tor\tor.exe",
        r"C:\Program Files (x86)\Tor Browser\Browser\TorBrowser\Tor\tor.exe",
        r"C:\Tor\tor.exe",
        r"C:\Program Files\Tor\tor.exe",
        r"C:\Program Files (x86)\Tor\tor.exe",
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Tor', 'tor.exe')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"[TOR Install] Found existing TOR: {path}")
            return path
    
    # Try to find in PATH
    try:
        result = subprocess.run(["where", "tor"], capture_output=True, text=True)
        if result.returncode == 0:
            tor_path = result.stdout.strip().split('\n')[0]
            print(f"[TOR Install] Found TOR in PATH: {tor_path}")
            return tor_path
    except:
        pass
    
    return None

def setup_tor():
    """Main TOR setup function"""
    print("[TOR Install] Setting up TOR...")
    
    # First, check if TOR is already available
    tor_path = find_system_tor()
    if tor_path:
        return tor_path
    
    # Try to install via package manager
    if os.name == 'nt':
        if install_tor_via_choco():
            tor_path = find_system_tor()
            if tor_path:
                return tor_path
    
    # Download and install manually
    tor_path = download_tor_windows()
    if tor_path:
        return tor_path
    
    print("[TOR Install] Failed to install TOR. Please install manually:")
    print("1. Download TOR Browser from https://www.torproject.org/download/")
    print("2. Or install via Chocolatey: choco install tor")
    print("3. Or download TOR Expert Bundle")
    
    return None

if __name__ == "__main__":
    tor_path = setup_tor()
    if tor_path:
        print(f"[TOR Install] TOR setup complete: {tor_path}")
        
        # Test TOR
        try:
            result = subprocess.run([tor_path, "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"[TOR Install] TOR version: {result.stdout.strip()}")
            else:
                print(f"[TOR Install] TOR test failed: {result.stderr}")
        except Exception as e:
            print(f"[TOR Install] TOR test error: {e}")
    else:
        print("[TOR Install] TOR setup failed")
