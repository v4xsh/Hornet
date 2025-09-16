#!/usr/bin/env python3
"""
Hornet AI Network Safety Setup Script
This script helps set up TOR and network safety features
"""

import os
import sys
import subprocess
import platform
import requests
import zipfile
import shutil


def print_banner():
    banner = """
    ╔═══════════════════════════════════════╗
    ║      HORNET AI NETWORK SAFETY         ║
    ║           SETUP WIZARD                ║
    ╔═══════════════════════════════════════╝
    """
    print(banner)


def check_admin():
    """Check if running with admin privileges"""
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.getuid() == 0


def install_requirements():
    """Install Python requirements"""
    print("\n📦 Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_network.txt"])
        print("✅ Python requirements installed successfully")
    except Exception as e:
        print(f"❌ Failed to install requirements: {e}")
        return False
    return True


def download_tor_windows():
    """Download and extract TOR for Windows"""
    print("\n📥 Downloading TOR for Windows...")
    
    tor_url = "https://www.torproject.org/dist/torbrowser/13.0.1/tor-expert-bundle-13.0.1-windows-x86_64.tar.gz"
    tor_path = os.path.join(os.path.dirname(__file__), "tor_bundle.tar.gz")
    
    try:
        # Download TOR
        response = requests.get(tor_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(tor_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = int((downloaded / total_size) * 100)
                    print(f"\rDownloading: {percent}%", end='')
        
        print("\n✅ TOR downloaded successfully")
        
        # Extract TOR
        print("📦 Extracting TOR...")
        import tarfile
        with tarfile.open(tor_path, 'r:gz') as tar:
            tar.extractall(os.path.dirname(__file__))
        
        os.remove(tor_path)
        print("✅ TOR extracted successfully")
        
        return True
    except Exception as e:
        print(f"❌ Failed to download/extract TOR: {e}")
        return False


def setup_tor_directory():
    """Create necessary directories for TOR"""
    dirs = ["tor_data", "hidden_service", "zeek_logs"]
    
    for dir_name in dirs:
        dir_path = os.path.join(os.path.dirname(__file__), dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"📁 Created directory: {dir_name}")


def configure_firewall():
    """Configure Windows Firewall for Hornet"""
    if platform.system() != "Windows":
        return
    
    print("\n🔥 Configuring Windows Firewall...")
    
    try:
        # Allow TOR
        subprocess.run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            "name=HornetTOR", "dir=in", "action=allow",
            "protocol=TCP", "localport=9050,9051"
        ], check=True)
        
        # Create Hornet firewall group
        subprocess.run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            "name=HornetFirewall", "dir=out", "action=allow",
            "program=%SystemRoot%\\system32\\svchost.exe"
        ], check=True)
        
        print("✅ Firewall configured successfully")
    except Exception as e:
        print(f"⚠️ Failed to configure firewall: {e}")


def test_tor_connection():
    """Test if TOR is working"""
    print("\n🧪 Testing TOR connection...")
    
    try:
        from stem import Signal
        from stem.control import Controller
        
        # Try to connect to TOR control port
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="HornetTor123")
            print("✅ TOR control connection successful")
            return True
    except Exception as e:
        print(f"❌ TOR connection test failed: {e}")
        print("   Make sure TOR is running")
        return False


def create_shortcuts():
    """Create desktop shortcuts for easy access"""
    if platform.system() == "Windows":
        try:
            import win32com.client
            
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # Create Hornet Network Safety shortcut
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(os.path.join(desktop, "Hornet Network Safety.lnk"))
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = os.path.join(os.path.dirname(__file__), "Hornet.py")
            shortcut.WorkingDirectory = os.path.dirname(__file__)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            print("✅ Desktop shortcut created")
        except:
            print("⚠️ Could not create desktop shortcut")


def main():
    print_banner()
    
    # Check admin privileges
    if not check_admin():
        print("⚠️ Warning: Running without administrator privileges")
        print("   Some features may not work properly")
        input("\nPress Enter to continue anyway...")
    
    # Step 1: Install requirements
    if not install_requirements():
        print("\n❌ Setup failed at requirements installation")
        return
    
    # Step 2: Setup directories
    setup_tor_directory()
    
    # Step 3: Download TOR for Windows
    if platform.system() == "Windows":
        response = input("\n📥 Download TOR for Windows? (y/n): ")
        if response.lower() == 'y':
            download_tor_windows()
    
    # Step 4: Configure firewall
    if platform.system() == "Windows":
        configure_firewall()
    
    # Step 5: Create shortcuts
    create_shortcuts()
    
    print("\n" + "="*50)
    print("✅ SETUP COMPLETE!")
    print("="*50)
    
    print("\n📝 Next steps:")
    print("1. Install TOR Browser or TOR Expert Bundle")
    print("2. Run TOR and ensure it's listening on port 9050")
    print("3. Use 'Go advanced mode' command to enable IP rotation")
    print("4. Use 'Enable hornet firewall' to start network monitoring")
    
    print("\n🎯 Available commands:")
    print("- 'What is my IP' - Show current public IP")
    print("- 'Go advanced mode' - Enable IP rotation every 10 seconds")
    print("- 'Enable onion mode' - Use TOR without rotation")
    print("- 'Network status' - Show current network configuration")
    print("- 'Demo firewall' - Run firewall demo mode")
    print("- 'Scan traffic' - Analyze incoming traffic")
    
    input("\nPress Enter to exit setup...")


if __name__ == "__main__":
    main()

