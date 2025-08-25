#!/usr/bin/env python3
"""
Test Network Safety Features
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.network_safety import network_safety
from core.text_to_speech import speak
import time
import subprocess
import json

def get_detailed_ip_info():
    """Get detailed IP information using PowerShell command"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Invoke-RestMethod -Uri "https://ipinfo.io/json"'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Parse the PowerShell output which comes in key-value pairs
            lines = result.stdout.strip().split('\n')
            ip_info = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    ip_info[key.strip()] = value.strip()
            return ip_info
        else:
            print(f"PowerShell command failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error getting detailed IP info: {e}")
        return None

def test_network_features():
    print("🔍 Testing Network Safety Features...\n")
    
    # Test 1: Get current IP
    print("Test 1: Getting current IP...")
    current_ip = network_safety.get_public_ip()
    print(f"✅ Current IP: {current_ip}")
    speak(f"Your current IP address is {current_ip}")
    time.sleep(2)
    
    # Detailed IP info before change
    print("\nDetailed IP info before change:")
    detailed_ip_info_before = get_detailed_ip_info()
    if detailed_ip_info_before:
        for key, value in detailed_ip_info_before.items():
            print(f"{key}: {value}")

    # Test 2: Switch to onion mode
    print("\nTest 2: Switching to onion mode...")
    network_safety.switch_mode("onion")
    time.sleep(5)
    
    # Test 3: Get new IP
    print("\nTest 3: Checking IP after enabling Tor...")
    new_ip = network_safety.get_public_ip()
    print(f"✅ New IP (via Tor): {new_ip}")
    
    if current_ip != new_ip:
        print("✅ SUCCESS: IP has changed! Tor is working!")
        speak("Tor is working correctly. Your IP has been changed.")
    else:
        print("⚠️ WARNING: IP hasn't changed. Tor might not be routing properly.")
        speak("Warning: Your IP hasn't changed.")
    
    # Detailed IP info after change
    print("\nDetailed IP info after change:")
    detailed_ip_info_after = get_detailed_ip_info()
    if detailed_ip_info_after:
        for key, value in detailed_ip_info_after.items():
            print(f"{key}: {value}")

    # Test 4: Get network status
    print("\nTest 4: Getting network status...")
    status = network_safety.get_network_status()
    print(f"Mode: {status['mode']}")
    print(f"Tor Active: {status['tor_active']}")
    print(f"Current IP: {status['current_ip']}")
    
    # Test 5: Switch back to standard mode
    print("\nTest 5: Switching back to standard mode...")
    network_safety.switch_mode("standard")
    time.sleep(2)
    
    print("\n✅ All tests completed!")
    speak("Network safety tests completed.")

if __name__ == "__main__":
    try:
        test_network_features()
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        speak("Error during network testing.")
