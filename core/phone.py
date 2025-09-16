import subprocess
import time
import re
import requests

# Import your existing WhatsApp functions
from core.whatsapp import send_whatsapp_message  # Only text messages

# Emergency contacts
EMERGENCY_CONTACTS = ["Yash"]

# ==========================
# Core Phone Functions
# ==========================
def is_phone_connected():
    try:
        result = subprocess.run(["adb", "get-state"], capture_output=True, text=True)
        return "device" in result.stdout.lower()
    except Exception:
        return False

def call_contact(name):
    cmd = [
        "adb", "shell", "am", "start",
        "-n", "com.hornet.callhelper/.CallActivity",
        "-a", "com.hornet.CALL_CONTACT",
        "--es", "name", name,
        "-f", "0x14008000"
    ]
    subprocess.run(cmd)
    print(f"Calling {name}.")

def open_app_on_phone(app_name):
    def get_installed_packages():
        result = subprocess.run(["adb", "shell", "pm", "list", "packages"], capture_output=True, text=True)
        return [line.replace("package:", "").strip() for line in result.stdout.splitlines()]

    app_name_clean = app_name.strip().lower().replace(" ", "")
    packages = get_installed_packages()
    matched_package = None

    for pkg in packages:
        cleaned_pkg = pkg.replace(".", "").lower()
        print(f"🔍 Checking package: {pkg}")
        if app_name_clean in cleaned_pkg or app_name_clean in pkg.lower():
            matched_package = pkg
            break

    if matched_package:
        cmd = [
            "adb", "shell", "monkey",
            "-p", matched_package,
            "-c", "android.intent.category.LAUNCHER",
            "1"
        ]
        subprocess.run(cmd)
        print(f"✅ Opened {matched_package}")
    else:
        print(f"❌ No match found for: {app_name}")

def lock_phone_screen():
    cmd = [
        "adb", "shell", "am", "start",
        "-n", "com.hornet.callhelper/.LockActivity",
        "-a", "com.hornet.LOCK_DEVICE",
        "-f", "0x14008000"
    ]
    subprocess.run(cmd)
    print("Locking phone.")

def send_phone_basic_action(action_name):
    cmd = [
        "adb", "shell", "am", "start",
        "-n", "com.hornet.callhelper/.BasicFeaturesActivity",
        "-a", "com.hornet.PHONE_COMMAND",
        "--es", "action_name", action_name,
        "-f", "0x14008000"
    ]
    subprocess.run(cmd)
    print(f"Sent phone command: {action_name}")

# ==========================
# Emergency Help Feature
# ==========================
def fetch_location_and_ip():
    """Fetch latest coordinates from HornetLocation logs and public IP"""
    try:
        # Force location ON
        subprocess.run(["adb", "shell", "settings", "put", "secure", "location_mode", "3"])
        print("✅ Location forced ON")

        # Wait a few seconds for location service to update
        time.sleep(5)

        # Fetch latest logs
        log_result = subprocess.run(
            ["adb", "logcat", "-d", "-s", "HornetLocation"],
            capture_output=True, text=True
        )
        lat, lng = None, None
        for line in reversed(log_result.stdout.splitlines()):
            match = re.search(r"Lat: ([\d\.-]+), Lng: ([\d\.-]+)", line)
            if match:
                lat, lng = match.group(1), match.group(2)
                break

        if lat is None or lng is None:
            print("❌ Failed to fetch coordinates")
            lat, lng = "Unknown", "Unknown"

        maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"

        # Fetch public IP
        try:
            ip = requests.get("https://api.ipify.org").text
        except Exception:
            ip = "Unknown"

        return lat, lng, maps_url, ip
    except Exception as e:
        print("❌ Error fetching location/IP:", e)
        return "Unknown", "Unknown", "Unknown", "Unknown"

def help_command():
    """Trigger emergency workflow"""
    if not is_phone_connected():
        print("❌ Phone not connected.")
        return

    lat, lng, maps_url, ip = fetch_location_and_ip()
    message = f"Hey, I need help! My location: {maps_url} (Lat: {lat}, Lng: {lng}), IP: {ip}"

    for contact in EMERGENCY_CONTACTS:
        try:
            send_whatsapp_message(contact, message)
        except Exception as e:
            print(f"❌ Failed to send message to {contact}: {e}")

