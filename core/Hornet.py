from core.face_auth import verify_face
from core.text_to_speech import speak
import asyncio
import pyttsx3
import edge_tts
from playsound import playsound
import speech_recognition as sr
import webbrowser
import wikipedia
import pywhatkit
import pygetwindow as gw
import pyautogui
import psutil
import os
import random
import tkinter as tk
from threading import Thread
from tkinter import PhotoImage, Scrollbar, Text, END, DISABLED, NORMAL
from PIL import Image, ImageTk, ImageSequence
import sys
import os
import subprocess
import platform
import google.generativeai as genai
import threading
import pygame
from core.text_to_speech import speak, start_buffering, stop_buffering
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import webbrowser
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import time
from scipy.io.wavfile import write
import numpy as np
from core.voice_auth import is_vansh_speaking
import sounddevice as sd
import scipy.io.wavfile as wav
import os
import soundfile as sf
import speech_recognition as sr
from core.voice_auth import is_vansh_speaking, record_voice
from screen_brightness_control import set_brightness, get_brightness
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
import cv2
from core.mail_assistant import handle_send_mail
from core.voice_capture import record_voice_dynamic
from core.basic_features import (
    take_screenshot, view_screenshot,
    change_volume, change_brightness
)
from core.command_handler import CommandHandler
from core.screen_recording import start_screen_recording, stop_screen_recording
import pyautogui
import pygame
import pyautogui
import time
import os
from core.text_to_speech import speak
from datetime import datetime
from playsound import playsound  # Works with WAV too

from core.utils import resource_path

import datetime
import pyautogui
import pygame
import os
from core.text_to_speech import speak
from core.screen_recording import start_screen_recording, stop_screen_recording, last_recording_path
from core.text_to_speech import speak
from core.screen_recording import (
    start_screen_recording,
    stop_screen_recording,
    get_last_recording_path
)

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import math
# screen_recording.py
import cv2
import pyautogui
import numpy as np
import threading

import threading
from core.enroll_voice import update_embedding

def should_rebuild_embedding(folder):
    try:
        emb_time = os.path.getmtime(os.path.join(folder, "vansh_embedding.pt"))
        latest_wav_time = max(os.path.getmtime(os.path.join(folder, f))
                              for f in os.listdir(folder)
                              if f.endswith(".wav") and f.startswith("sample_"))
        return latest_wav_time > emb_time
    except Exception:
        return True  # No embedding or error

def start_background_embedding_update():
    folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "voice_data")
    if should_rebuild_embedding(folder):
        print("🔄 Detected newer voice samples — updating embedding in background...")
        threading.Thread(target=update_embedding, name="StartupEmbeddingUpdater", daemon=True).start()
    else:
        print("✅ Embedding already up to date.")

# 🔁 Run this once on app start (non-blocking)
start_background_embedding_update()
recording = False
recording_thread = None
def listen(self):
        from core.voice_auth import record_voice
        import speech_recognition as sr

        record_voice_dynamic("temp_voice.wav")

        r = sr.Recognizer()
        with sr.AudioFile("temp_voice.wav") as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.record(source)
        try:
            command = r.recognize_google(audio)
            print("You said:", command)
            return command.lower()
        except:
            return "error"

def process_command(self, command):
        if "youtube" in command:
            import webbrowser
            webbrowser.open("https://www.youtube.com")
            self.ui.show_waifu_response("Opening YouTube...")
        else:
            self.ui.show_waifu_response("Unknown command.")
def listen_and_record():
    # speak("Listening...")
    filename = "temp_voice.wav"

    duration = 2  # adjust if needed
    fs = 44100

    # Record voice
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write(filename, recording, fs)
    print("Voice recorded to", filename)

    # Transcribe using Google Speech Recognition
    r = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.record(source)
        try:
            command = r.recognize_google(audio)
            print("You said:", command)
            return command
        except sr.UnknownValueError:
            speak("Sorry, I didn't understand that.")
            return ""
        except sr.RequestError:
            speak("Could not request results.")
            return ""
def record_temp_voice(duration=2, filename="temp_voice.wav"):
    fs = 44100  # High-quality sample rate
    print("Recording voice...")
    
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is done

    # Check if recording is audible (not silence)
    if np.max(np.abs(recording)) < 1000:
        raise Exception("Recording too quiet. Please speak louder.")

    # Save to temp file
    wav.write(filename, fs, recording)
    print(f"Voice recorded to {filename}")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


listener = sr.Recognizer()

engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)

def listen_command():
    with sr.Microphone() as source:
        print("Listening...")
        listener.adjust_for_ambient_noise(source)
        audio = listener.listen(source, phrase_time_limit=5)
    try:
        command = listener.recognize_google(audio).lower()
        print("You:", command)
        return command
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return "network error"

def search_anything(command):
    if "search" in command:
        command = command.lower()

        query = command.replace("search", "").replace("for", "").strip()

        if "youtube" in command:
            query = query.replace("on youtube", "").strip()
            speak(f"Searching YouTube for {query}")
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")

        elif "chat gpt" in command:
            query = query.replace("on chat gpt", "").strip()
            speak(f"Searching ChatGPT for {query}")
            webbrowser.open(f"https://chat.openai.com/?q={query}")

        else:
            query = query.replace("on google", "").strip()
            speak(f"Searching Google for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")



def time_based_greeting():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        speak("Good morning! Vansh How can I help you today?")
    elif 12 <= hour < 17:
        speak("Good afternoon vansh")
        time.sleep(0.001)
        speak("how are you doing?")
    elif 17 <= hour < 22:
        speak("Good evening vansh! 🌆 Need any assistance?")
    else:
        speak("Hello! It's quite late. Do you need help with something?")

def handle_small_talk(command):
    command = command.lower()
    for key in responses:
        if key in command:
            speak(random.choice(responses[key]))
            return True
    return False

class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hornet AI")
        self.root.geometry("800x700")
        self.root.configure(bg="black")
        self.root.resizable(False, False)
        self.root.wm_attributes("-topmost", True)
        self.command_handler = CommandHandler(self)
        self.canvas = tk.Canvas(self.root, width=800, height=700, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        gif = Image.open(resource_path("assets/goku.gif"))
        frame_size = (800, 600)
        self.frames = [ImageTk.PhotoImage(img.resize(frame_size, Image.LANCZOS).convert('RGBA'))
                       for img in ImageSequence.Iterator(gif)]
        self.gif_index = 0
        self.bg_image = self.canvas.create_image(0, 0, anchor='nw', image=self.frames[0])
        self.animate()

        self.root.configure(bg="#000000")
        

        self.chat_log = Text(
            self.root,
            
            bg="#000000",
            fg="sky blue",
            font=("Consolas", 10,),
            wrap='word',
            
            bd=0
        )
        self.chat_log.place(x=0, y=600, width=800, height=100)
        self.chat_log.insert(END, "[System] Type your command below or press F2 to speak.\n")
        self.chat_log.config(state=tk.DISABLED)

        scrollbar = Scrollbar(self.chat_log)
        scrollbar.pack(side="right", fill="y")

        self.entry = tk.Entry(self.root, font=("Segoe UI", 13), bg="#1a1a1a", fg="white", bd=3, insertbackground='white')
        self.entry.place(x=20, y=670, width=700, height=30)
        self.entry.bind("<Return>", self.send_text)

        send_button = tk.Button(self.root, text="Send", command=self.send_text, bg="#222222", fg="white", relief='flat')
        send_button.place(x=730, y=670, width=50, height=30)

        self.root.bind("<F2>", lambda e: Thread(target=self.listen_voice).start())
        Thread(target=lambda: time_based_greeting()).start()
        self.start_wake_word_listener()

    def start_wake_word_listener(self):
      def _listen():
        from core.speech_recognition_proxy import proxy_aware_sr

        while True:
            try:
                trigger = proxy_aware_sr.listen_with_microphone(timeout=10, phrase_time_limit=3)
                if trigger and trigger != "error":
                    print("Heard:", trigger)

                    if "hey hornet" in trigger or trigger.strip() == "hornet":
                        print("🔔 Wake word detected")
                        self.add_text("[System] Wake word detected. Listening and verifying...")

                        # continue to voice capture + verification
                        from core.voice_auth import is_vansh_speaking, cleanup_temp_voice
                        from core.voice_capture import record_voice_dynamic

                        success, path, match_status = record_voice_dynamic(timeout=8, preserve_temp=True)
                        if not success or not path:
                            # speak("No command detected.")
                            continue

                        if match_status != "match":
                            speak("Voice not verified. Try again.")
                            self.add_text("[Security] Unauthorized voice.")
                            cleanup_temp_voice(path)
                            continue

                        
                        speak("Voice matched. Processing command.")
                        self.add_text("[Security] Voice matched. Processing command...")

                        # Use proxy-aware speech recognition
                        command = proxy_aware_sr.recognize_audio(path)
                        if command and command != "network error":
                            print("You said:", command)
                            self.add_text("You: " + command)
                            Thread(target=lambda: self.command_handler.handle_text(command)).start()
                        elif command == "network error":
                            self.add_text("[Error] Network connectivity issue")
                        else:
                            speak("Sorry, I didn't catch that.")
                        
                        cleanup_temp_voice(path)

            except Exception as e:
                print("Wake error:", e)
                continue

            time.sleep(0.2)

      Thread(target=_listen, daemon=True).start()



    def animate(self):
        self.canvas.itemconfig(self.bg_image, image=self.frames[self.gif_index])
        self.gif_index = (self.gif_index + 1) % len(self.frames)
        self.root.after(100, self.animate)


    def send_text(self, event=None):
        user_input = self.entry.get()
        self.entry.delete(0, END)
        if user_input:
            self.add_text("You: " + user_input)
            Thread(target=lambda: self.command_handler.handle_text(user_input)).start()


    def add_text(self, text):
        self.chat_log.config(state=tk.NORMAL)
        self.chat_log.insert(END, text + "\n")
        self.chat_log.config(state=tk.DISABLED)
        self.chat_log.see(END)

    def listen_voice(self):
        self.add_text("[System] Listening...")
        Thread(target=self.command_handler.handle).start()
        # command = listen_command()
        # if command:
        #     self.add_text("You: " + command)
        #     Thread(target=lambda: self.command_handler.handle(command)).start()
def cleanup_on_exit():
    """Cleanup network settings when app exits"""
    try:
        from core.network_safety import network_safety
        print("[Cleanup] Restoring network settings...")
        network_safety.switch_mode("standard")
        print("[Cleanup] Network cleanup completed")
    except Exception as e:
        print(f"[Cleanup] Error during network cleanup: {e}")

def main():
    import atexit
    import signal

    

    # Register cleanup function to run on exit
    atexit.register(cleanup_on_exit)
    
    # Handle Ctrl+C and other signals
    def signal_handler(signum, frame):
        print("\n[Exit] Received exit signal, cleaning up...")
        cleanup_on_exit()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        root = tk.Tk()
        app = AssistantGUI(root)
        
        # Handle window close event
        def on_closing():
            print("[Exit] Window closing, cleaning up...")
            cleanup_on_exit()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    except Exception as e:
        print(f"[Error] Application error: {e}")
        cleanup_on_exit()
    finally:
        print("[Exit] Application terminated")


if __name__ == "__main__":
    main()
