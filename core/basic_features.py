import os
import time
import datetime
import pyautogui
import pygame
import screen_brightness_control as sbc
from core.text_to_speech import speak
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from core.utils import resource_path
import ctypes
import winshell

# ✅ CORRECTED IMPORTS: Using the new, streamlined voice capture function
from core.voice_capture import record_and_transcribe

# Screenshot setup
home_dir = os.path.expanduser("~")
screenshot_dir = os.path.join(home_dir, "OneDrive", "Pictures", "Screenshots")
os.makedirs(screenshot_dir, exist_ok=True)
last_screenshot_path = None

def take_screenshot():
    global last_screenshot_path
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshot_{timestamp}.png"
        path = os.path.join(screenshot_dir, filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        try:
            pygame.mixer.music.load(resource_path("assets/camera_click.wav"))
            pygame.mixer.music.play()
        except Exception as e:
            print("🔊 Sound Error:", e)
            speak("Screenshot saved, but couldn't play sound.")
        else:
            speak("Screenshot taken and saved.")
        last_screenshot_path = path
    except Exception as e:
        print("❌ Screenshot Error:", e)
        speak("Something went wrong while taking the screenshot.")

def view_screenshot():
    try:
        global last_screenshot_path
        if last_screenshot_path and os.path.exists(last_screenshot_path):
            os.startfile(last_screenshot_path)
        else:
            speak("Sorry, I couldn't find the screenshot.")
    except Exception as e:
        print("❌ View Error:", e)
        speak("I couldn't open the screenshot.")

# Volume
def show_volume_popup():
    pyautogui.press("volumedown")
    time.sleep(0.05)
    pyautogui.press("volumeup")

def change_volume(direction=None, percent=None):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    if percent is not None:
        level = max(0.0, min(percent / 100.0, 1.0))
        volume.SetMasterVolumeLevelScalar(level, None)
        show_volume_popup()
        speak(f"Volume set to {percent} percent.")
    else:
        current = volume.GetMasterVolumeLevelScalar()
        step = 0.1
        if direction == "up":
            volume.SetMasterVolumeLevelScalar(min(current + step, 1.0), None)
            show_volume_popup()
            speak("Volume increased.")
        elif direction == "down":
            volume.SetMasterVolumeLevelScalar(max(current - step, 0.0), None)
            show_volume_popup()
            speak("Volume decreased.")

# Brightness
def show_brightness_popup():
    # This is a trick to show the brightness slider; requires a laptop keyboard with brightness keys.
    # It might not work on all systems.
    try:
        sbc.set_brightness(sbc.get_brightness()[0])
    except Exception:
        pass # Ignore if it fails, as it's just for UI feedback

def change_brightness(direction=None, percent=None):
    if percent is not None:
        sbc.set_brightness(min(max(percent, 0), 100))
        show_brightness_popup()
        speak(f"Brightness set to {percent} percent.")
    else:
        try:
            current = sbc.get_brightness(display=0)[0]
            step = 10
            if direction == "up":
                sbc.set_brightness(min(current + step, 100))
                show_brightness_popup()
                speak("Brightness increased.")
            elif direction == "down":
                sbc.set_brightness(max(current - step, 0))
                show_brightness_popup()
                speak("Brightness decreased.")
        except Exception as e:
            speak("Sorry, I couldn't change the display brightness.")
            print(f"Brightness control error: {e}")

# Recycle Bin - Open
def open_recycle_bin():
    try:
        os.system("start shell:RecycleBinFolder")
        speak("Recycle bin opened.")
    except Exception as e:
        print("❌ Recycle bin open error:", e)
        speak("Failed to open the recycle bin.")

# ✅ CORRECTED: Replaced old logic with the new, single-function call
def ask_yes_no(prompt):
    """Asks a yes/no question and returns True for yes, False for no."""
    reply = record_and_transcribe(prompt=prompt, duration=5)
    return "yes" in reply or "yeah" in reply or "sure" in reply or "confirm" in reply

# Recycle Bin - Empty with confirmation
def empty_recycle_bin():
    try:
        items = list(winshell.recycle_bin())
        count = len(items)

        if count == 0:
            speak("Recycle bin is already empty.")
            return

        # Uses the corrected ask_yes_no function
        confirmed = ask_yes_no(f"Are you sure you want to permanently delete {count} items from the recycle bin?")
        
        if not confirmed:
            speak("Okay, I won't empty the recycle bin.")
            return

        # Use the high-level winshell function for emptying, it's safer.
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        speak(f"Deleted {count} items from the recycle bin.")

    except Exception as e:
        print("❌ Recycle bin empty error:", e)
        speak("An error occurred while emptying the recycle bin.")