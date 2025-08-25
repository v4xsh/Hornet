import os
import cv2
import time
import platform
import pyautogui
import subprocess
import numpy as np
import threading
from datetime import datetime
from core.text_to_speech import speak
import pygame
from pathlib import Path  # ✅ Import pathlib for dynamic user paths

# 🔹 Global variables
last_recording_path = None
recording = False
recording_thread = None

# 🔹 Initialize pygame mixer (for audio use elsewhere)
pygame.mixer.init()

def screen_record(output_path):
    global recording
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(output_path, fourcc, 20.0, screen_size)

    while recording:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)

    out.release()

def start_screen_recording():
    global recording, recording_thread, last_recording_path

    recording = True
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # ✅ Use user's Videos folder
    video_dir = Path.home() / "Videos" / "Screen Recordings"
    os.makedirs(video_dir, exist_ok=True)

    last_recording_path = os.path.join(str(video_dir), f"screen_record_{timestamp}.avi")

    recording_thread = threading.Thread(target=screen_record, args=(last_recording_path,))
    recording_thread.start()

    speak("Screen recording started. Say 'stop screen recording' to end.")

def stop_screen_recording():
    global recording, recording_thread

    if recording:
        recording = False
        recording_thread.join()
        speak("Screen recording stopped and saved.")
        speak("You can say 'view recording' if you want me to show it.")
    else:
        speak("No active recording to stop.")

def get_last_recording_path():
    global last_recording_path
    return last_recording_path

def view_recording():
    try:
        path = get_last_recording_path()
        print("📝 Last recording path:", path)

        if path and os.path.exists(path):
            if platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
            speak("Opening your recording now.")
        else:
            speak("Sorry, I couldn't find the recording.")
    except Exception as e:
        print("❌ View Recording Error:", e)
        speak("I couldn't open the recording.")
