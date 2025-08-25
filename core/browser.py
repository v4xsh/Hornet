import webbrowser
import subprocess
import time
import pygetwindow as gw
import pyautogui
from core.text_to_speech import speak

def open_any_website(command):
    known_sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "instagram": "https://www.instagram.com",
        "chatgpt": "https://chat.openai.com",
        "github": "https://github.com",
        "spotify": "https://open.spotify.com"
    }
    for name, url in known_sites.items():
        if name in command:
            speak(f"Opening {name}")
            webbrowser.open(url)
            return True

    if "open" in command:
        site = command.split("open")[-1].strip().replace(" ", "")
        url = f"https://www.{site}.com"
        speak(f"Trying to open {site}")
        webbrowser.open(url)
        return True

    return False

def close_application(command):
    keyword = command.replace("close", "").replace("app", "").strip().lower()
    found = False

    for window in gw.getWindowsWithTitle(''):
        title = window.title.lower()
        if keyword in title:
            try:
                window.close()
                speak(f"Closed window with {keyword}")
                found = True
                break
            except:
                continue

    if not found:
        speak(f"No window found containing '{keyword}'")

def search_in_chrome(query):
    try:
        # Step 1: Try to find and focus Chrome window
        chrome_found = False
        for win in gw.getWindowsWithTitle("Chrome"):
            if "chrome" in win.title.lower():
                win.activate()
                chrome_found = True
                break

        # Step 2: If Chrome not open, open it
        if not chrome_found:
            subprocess.Popen("start chrome", shell=True)
            time.sleep(3)  # wait for Chrome to load
            win_list = gw.getWindowsWithTitle("Chrome")
            if win_list:
                win_list[0].activate()
        
        time.sleep(1)

        # Step 3: Open new tab (Ctrl + T)
        pyautogui.hotkey('ctrl', 't')
        time.sleep(0.5)

        # Step 4: Type query
        pyautogui.write(query, interval=0.05)
        pyautogui.press('enter')

    except Exception as e:
        print("❌ Error during Chrome automation:", e)
        speak("Sorry, I couldn't complete the search.")
