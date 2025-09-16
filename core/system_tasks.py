import os
import subprocess
import glob
from core.text_to_speech import speak

def perform_system_task(command):
    command = command.lower()

    # 🔹 Open apps
    if "open notepad" in command:
        os.system("start notepad")
        speak("Opening Notepad")
        return True

    elif "open calculator" in command:
        os.system("start calc")
        speak("Opening Calculator")
        return True

    elif "open chrome" in command:
        user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
        profile_dirs = glob.glob(os.path.join(user_data_dir, "*"))

        # Filter only valid Chrome profiles
        valid_profiles = [
            d for d in profile_dirs
            if os.path.isdir(d) and (os.path.basename(d).lower().startswith("profile") or os.path.basename(d).lower() == "default")
        ]

        if not valid_profiles:
            speak("No Chrome profiles found.")
            return True

        # Find the most recently modified profile
        most_recent_profile = max(valid_profiles, key=os.path.getmtime)
        selected_profile = os.path.basename(most_recent_profile)

        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

        if os.path.exists(chrome_path):
            speak(f"Opening Chrome with your recent profile: {selected_profile}")
            subprocess.Popen([chrome_path, f"--profile-directory={selected_profile}"])
        else:
            speak("Google Chrome executable not found.")
        return True

    elif "open paint" in command:
        os.system("start mspaint")
        speak("Opening Paint")
        return True

    elif "open cmd" in command or "open command prompt" in command:
        os.system("start cmd")
        speak("Opening Command Prompt")
        return True

    elif "open vscode" in command or "open code" in command or "open vs code" in command:
      open_new_window = "new window" in command

      try:
        args = ["code"]
        if open_new_window:
            args.append("--new-window")
        subprocess.Popen(args)
        speak("Opening Visual Studio Code" + (" in a new window" if open_new_window else ""))
        return True
      except FileNotFoundError:
        possible_paths = [
            os.path.expandvars(r"%LocalAppData%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft VS Code\Code.exe"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                args = [path]
                if open_new_window:
                    args.append("--new-window")
                subprocess.Popen(args)
                speak("Opening Visual Studio Code" + (" in a new window" if open_new_window else ""))
                return True

        speak("VS Code not found on this system.")
        return True



    # 🔹 Shutdown / Restart / Lock
    elif "shutdown" in command or "shut down" in command:
        speak("Shutting down the system.")
        os.system("shutdown /s /t 1")
        return True

    elif "restart" in command:
        speak("Restarting the system.")
        os.system("shutdown /r /t 1")
        return True

    elif "lock" in command or "lock screen" in command:
        speak("Locking the screen.")
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        return True

    # 🔹 Open folders
    elif "open downloads" in command:
        os.startfile(os.path.join(os.path.expanduser("~"), "Downloads"))
        speak("Opening Downloads folder.")
        return True

    elif "open documents" in command:
        os.startfile(os.path.join(os.path.expanduser("~"), "Documents"))
        speak("Opening Documents folder.")
        return True

    elif "open desktop" in command:
        os.startfile(os.path.join(os.path.expanduser("~"), "Desktop"))
        speak("Opening Desktop.")
        return True

    return False

