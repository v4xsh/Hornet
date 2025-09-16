#!/usr/bin/env python3
"""
Download and Install Tor for Windows
"""

import os
import requests
import zipfile
import tarfile
import shutil
from tqdm import tqdm

def download_tor():
    # Updated URL for Tor Expert Bundle
    tor_url = "https://dist.torproject.org/torbrowser/14.0.4/tor-expert-bundle-windows-x86_64-14.0.4.tar.gz"
    
    print("📥 Downloading Tor Expert Bundle...")
    
    # Download file
    response = requests.get(tor_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    tar_path = "tor_bundle.tar.gz"
    
    with open(tar_path, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    print("✅ Download complete!")
    
    # Extract tar.gz
    print("📦 Extracting Tor...")
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(".")
    
    # Clean up
    os.remove(tar_path)
    
    # Check if extraction was successful
    if os.path.exists("tor"):
        print("✅ Tor extracted successfully!")
        
        # Create torrc file
        create_torrc()
        
        print("\n🎯 Tor is ready to use!")
        print(f"📂 Tor location: {os.path.abspath('tor')}")
        print("🚀 You can now use 'tor\\tor.exe' to start Tor")
    else:
        print("❌ Failed to extract Tor")

def create_torrc():
    """Create a basic torrc configuration file"""
    torrc_content = """# Hornet AI Tor Configuration
SocksPort 9050
ControlPort 9051
HashedControlPassword 16:872860B76453A77D60CA2BB8C1A7042072093276A3D701AD684053EC4C

# Circuit settings for IP rotation
MaxCircuitDirtiness 10
NewCircuitPeriod 10
CircuitBuildTimeout 10
LearnCircuitBuildTimeout 0
CircuitStreamTimeout 10

# Logging
Log notice file ./tor_notices.log

# Data directory
DataDirectory ./tor_data
"""
    
    with open("torrc", "w") as f:
        f.write(torrc_content)
    
    print("✅ Created torrc configuration file")

if __name__ == "__main__":
    try:
        # Install tqdm if not available
        import subprocess
        subprocess.run(["pip", "install", "tqdm"], capture_output=True)
        
        download_tor()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📝 Manual installation steps:")
        print("1. Download Tor Browser from https://www.torproject.org/download/")
        print("2. Or download Tor Expert Bundle for command-line use")
        print("3. Extract to this directory")

