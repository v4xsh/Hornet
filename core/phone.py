import subprocess

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
