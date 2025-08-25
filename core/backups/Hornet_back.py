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


def cleanup_temp_voice():
    try:
        if os.path.exists("temp_voice.wav"):
            os.remove("temp_voice.wav")
            print("🧽 Temp voice cleaned.")
    except Exception as e:
        print("Error during cleanup:", e)

def listen_and_record():
    speak("Listening...")
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

def search_and_type_on_site(site, query):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    if site == "youtube":
        driver.get("https://www.youtube.com")
        time.sleep(3)
        search_box = driver.find_element(By.NAME, "search_query")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        return driver  # ✅ Return driver so it can be reused

    elif site == "wikipedia":
        driver.get("https://www.wikipedia.org")
        time.sleep(2)
        search_box = driver.find_element(By.NAME, "search")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

    elif site == "twitter":
        driver.get("https://twitter.com/explore")
        time.sleep(3)
        search_box = driver.find_element(By.XPATH, '//input[@aria-label="Search query"]')
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

    elif site == "chatgpt":
        driver.get("https://chat.openai.com")

    elif site == "instagram":
        driver.get("https://www.instagram.com")

    else:
        driver.get(f"https://www.{site}.com")

    return None  # Return None if not YouTube

        # Generic fallback

    # Optional: Add driver.quit() after some time if you don’t want to keep the browser open
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def play_top_youtube_video(query, driver):
    try:
        # Focus YouTube and perform new search
        driver.get("https://www.youtube.com")  # reload YouTube homepage
        time.sleep(2)
        search_box = driver.find_element(By.NAME, "search_query")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)

        videos = driver.find_elements(By.ID, "video-title")
        if videos:
            videos[0].click()
        else:
            speak("No videos found.")
    except Exception as e:
        speak("An error occurred while trying to play the video.")
        print(f"[YouTube Play Error] {e}")


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
        print("Error during Chrome automation:", e)

def send_whatsapp_message(contact_name, message):
    chrome_driver_path = "C:/drivers/chromedriver-win64/chromedriver.exe"
    brave_path = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"

    options = webdriver.ChromeOptions()
    options.binary_location = brave_path

    # ✅ Use real Brave profile where WhatsApp is already logged in
    options.add_argument("user-data-dir=C:/Users/Vansh/AppData/Local/BraveSoftware/Brave-Browser/User Data")
    options.add_argument("profile-directory=Default")

    # ✅ These flags help prevent crashing
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # ✅ Now launch Brave via ChromeDriver
    try:
        driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    except Exception as e:
        print("❌ Failed to launch Brave via ChromeDriver:", e)
        return

    # ✅ Open WhatsApp Web
    driver.get("https://web.whatsapp.com")

    try:
        # ✅ Wait until search bar is ready
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
        )
    except Exception as e:
        print("❌ WhatsApp Web didn't load properly:", e)
        return

    # ✅ Search and message logic
    try:
        search_box = driver.find_element(By.XPATH, "//div[@contenteditable='true'][@data-tab='3']")
        search_box.click()
        search_box.send_keys(contact_name)
        time.sleep(2)
        search_box.send_keys(Keys.ENTER)
        message_box_xpath = "//div[@contenteditable='true'][@data-tab='10']"
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, message_box_xpath))
        )
        message_box = driver.find_element(By.XPATH, message_box_xpath)
        message_box.click()
        message_box.send_keys(message)
        message_box.send_keys(Keys.ENTER)

        print(f"✅ Message sent to {contact_name}")
    except Exception as e:
        print("❌ Error sending message:", e)

pygame.mixer.init()
audio_lock = threading.Lock()

buffering = False
buffering_thread = None
def play_buffering_sound():
    pygame.mixer.music.load("buffering.wav")
    with audio_lock:
        pygame.mixer.music.play(-1) 
    while buffering:
        time.sleep(0.1)

def start_buffering():
    global buffering, buffering_thread
    if not buffering:
        buffering = True
        buffering_thread = threading.Thread(target=play_buffering_sound)
        buffering_thread.start()

def stop_buffering():
    global buffering
    buffering = False
    with audio_lock:
        pygame.mixer.music.stop()
    time.sleep(0.3)

GEMINI_API_KEY = "AIzaSyAi3RFimnFMykgvNuQE9bf9pseEFVdp0zw"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")
def get_gemini_response(prompt):
    try:
        response = gemini_model.generate_content(prompt)
        full_reply = response.text.strip()
        short_reply = full_reply[:300].split(".")[0].replace("*", "") + "."
        stop_buffering()
        speak(short_reply)
        return short_reply

    except Exception as e:
        stop_buffering()
        print("Gemini Error:", e)
        return "Sorry, I couldn't think of a reply right now."
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


listener = sr.Recognizer()


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
        os.system("start chrome")
        speak("Opening Chrome")
        return True

    elif "open paint" in command:
        os.system("start mspaint")
        speak("Opening Paint")
        return True

    elif "open cmd" in command or "open command prompt" in command:
        os.system("start cmd")
        speak("Opening Command Prompt")
        return True

    elif "open vscode" in command or "open code" in command:
        os.system("start code")
        speak("Opening VS Code")
        return True

    # 🔹 Shutdown / Restart / Lock
    elif "shutdown" in command:
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

    # 🔹 Open folder
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


engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)

def speak(text):
    with audio_lock:
        print("AI:", text)
        engine.say(text)
        engine.runAndWait()

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

import pygetwindow as gw

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


def repeat_after_me(command):
        if "repeat after me" in command:
           to_repeat = command.split("repeat after me ",)[-1].strip()
        elif "say" in command:
           to_repeat = command.split("say",)[-1].strip()
        else:
            return False

        if to_repeat:
           speak(to_repeat)
           return True

        return False

def tell_about_topic(command):
    trigger_phrases = ["do you know about", "tell me about", "who is", "what do you know about"]
    for phrase in trigger_phrases:
        if phrase in command.lower():
            try:
                topic = command.lower()
                for p in trigger_phrases:
                    topic = topic.replace(p, "")
                topic = topic.strip()
                summary = wikipedia.summary(topic, sentences=2)
                speak(summary)
            except wikipedia.exceptions.DisambiguationError:
                speak(f"There are multiple entries for {topic}. Please be more specific.")
            except wikipedia.exceptions.PageError:
                speak(f"I couldn't find any information about {topic}.")
            return True
    return False

def explain_meaning(command):
    trigger_phrases = ["what do you mean by", "define", "explain","what is"]
    for phrase in trigger_phrases:
        if phrase in command.lower():
            try:
                topic = command.lower()
                for p in trigger_phrases:
                    topic = topic.replace(p, "")
                topic = topic.strip()
                summary = wikipedia.summary(topic, sentences=2)
                speak(summary)
            except wikipedia.exceptions.DisambiguationError:
                speak(f"There are multiple meanings of {topic}. Can you be more specific?")
            except wikipedia.exceptions.PageError:
                speak(f"I couldn't find the meaning of {topic}.")
            return True
    return False


import re


def set_timer(command):
    pattern = r"timer for (\d+)\s*(seconds|second|minutes|minute)"
    match = re.search(pattern, command.lower())
    if match:
        value = int(match.group(1))
        unit = match.group(2)

        seconds = value if "second" in unit else value * 60
        speak(f"Timer set for {value} {unit}")
        time.sleep(seconds)
        speak(f"Time's up! Your {value} {unit} timer has finished.")
    else:
        speak("Sorry, I couldn't understand the timer duration.")



import datetime

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


import re

def extract_contact_and_message(command):
    match = re.match(r"(message|send)\s+(\w+)\s+(.*)", command.lower())
    if match:
        contact = match.group(2).capitalize()
        message = match.group(3).strip()
        return contact, message
    return None, None

def tell_about_person(command):
    name = command.replace("tell me about", "").replace("who is", "").strip()
    try:
        summary = wikipedia.summary(name, sentences=2)
        speak(summary)
    except wikipedia.exceptions.DisambiguationError:
        speak(f"There are multiple people named {name}. Please be more specific.")
    except wikipedia.exceptions.PageError:
        speak(f"I couldn't find any information about {name}.")

import pyautogui

def play_song_on_spotify(command):
    if "play" in command and "spotify" in command:
        song = command.replace("play", "").replace("on spotify", "").strip()
        speak(f"Playing {song} on Spotify")
        webbrowser.open(f"https://open.spotify.com/search/{song}")
        time.sleep(5)  
        pyautogui.press('tab', presses=5, interval=0.3)
        pyautogui.press('enter')
        time.sleep(1)
        pyautogui.press('space')


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
        self.root.title("VIONEX AI")
        self.root.geometry("800x700")
        self.root.configure(bg="black")
        self.root.resizable(False, False)
        self.root.wm_attributes("-topmost", True)
        


        self.canvas = tk.Canvas(self.root, width=800, height=700, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        gif = Image.open(resource_path("goku.gif"))
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


    def animate(self):
        self.canvas.itemconfig(self.bg_image, image=self.frames[self.gif_index])
        self.gif_index = (self.gif_index + 1) % len(self.frames)
        self.root.after(100, self.animate)


    def send_text(self, event=None):
        user_input = self.entry.get()
        self.entry.delete(0, END)
        if user_input:
            self.add_text("You: " + user_input)
            Thread(target=lambda: self.handle_command(user_input)).start()


    def add_text(self, text):
        self.chat_log.config(state=tk.NORMAL)
        self.chat_log.insert(END, text + "\n")
        self.chat_log.config(state=tk.DISABLED)
        self.chat_log.see(END)

    def listen_voice(self):
        self.add_text("[System] Listening...")
        Thread(target=self.handle_command).start()
        # command = listen_command()
        # if command:
        #     self.add_text("You: " + command)
        #     Thread(target=lambda: self.handle_command(command)).start()

    def handle_command(self):
        try:
             speak("Listening...")
             record_voice("temp_voice.wav", duration=3)
             
             r = sr.Recognizer()
             with sr.AudioFile("temp_voice.wav") as source:
               audio = r.record(source)
               try:
                 command = r.recognize_google(audio)
                 print("You said:", command)
                 self.add_text("You: " + command)
               except sr.UnknownValueError:
                speak("Sorry, I didn't understand that.")
                # cleanup_temp_voice()
                return
               except sr.RequestError:
                speak("Speech recognition error.")
                # cleanup_temp_voice()
                return
             speak("Verifying your voice...")
             if not is_vansh_speaking("temp_voice.wav"):
              self.add_text("[Security] Unauthorized voice.")
              speak("I'm sorry, only Vansh can access me. You're not Vansh.")
              return
             speak("Voice verified. Processing your command...")
             command = command.lower().strip()

        
        except Exception as e:
             self.add_text("[Security Error] Voice check failed.")
             speak("Voice verification failed. Try again.")
             return
        finally:
             cleanup_temp_voice()
        command = command.lower().strip()
        if command == "network error":
            self.add_text("[System] Network error")
            speak("Network error.")
            return
         # WhatsApp message
        contact, message = extract_contact_and_message(command)
        if contact and message:
          self.add_text(f"Sending WhatsApp message to {contact}: {message}")
          speak(f"Sending your message to {contact}")
          try:
             send_whatsapp_message(contact, message)
          except Exception as e:
            speak("Failed to send the WhatsApp message.")
            self.add_text(f"[Error] {e}")
          return
        # Check for follow-up video play request
        if hasattr(self, 'waiting_for_video_prompt') and self.waiting_for_video_prompt:
          self.waiting_for_video_prompt = False
          follow_up = command.replace("play", "").strip()
          if hasattr(self, 'last_search_query') and hasattr(self, 'youtube_driver'):
             combined = f"{self.last_search_query} {follow_up}"
             speak(f"Playing top YouTube video for {combined}")
             play_top_youtube_video(combined, self.youtube_driver)
          else:
             speak("I couldn't remember your last search.")
          return

         # Dynamic open and search (YouTube etc.)
        if "open" in command and "and search" in command:
          parts = command.replace("open", "").split("and search")
          website = parts[0].strip()
          query = parts[1].strip()
          speak(f"Opening {website} and searching for {query}")
          search_and_type_on_site(website, query)
          return
        #System task
        system_task_done = perform_system_task(command)
        if system_task_done:
            return
        #search for youtube video
        if "search" in command and "for" in command:
          parts = command.split("for")
          site_part = parts[0].replace("search", "").strip()
          query = parts[1].strip()
    
          if any(site in site_part for site in ["youtube", "instagram", "chatgpt", "twitter", "wikipedia"]):
            for site in ["youtube", "instagram", "chatgpt", "twitter", "wikipedia"]:
               if site in site_part:
                speak(f"Searching {site} for {query}")
                driver = search_and_type_on_site(site, query) 
                
                if site == "youtube":
                    
                    self.last_search_query = query
                    self.youtube_driver = driver
                    speak("Do you want me to play a specific video?")
                    self.waiting_for_video_prompt = True

                return
        elif "search" in command:
          search_term = command.replace("search", "").strip()
          speak(f"Searching for {search_term}")
          search_in_chrome(search_term)
          return
        # if search_in_browser_dynamic(command):
        #   return

        if "open" in command:
            if open_any_website(command):
                return

        if "close" in command:
            close_application(command)
            return
        
        if "timer" in command:
           set_timer(command)
           return

        if repeat_after_me(command):
           return

        # if "search" in command:
        #     search_anything(command)
        #     return
        
        if explain_meaning(command):
           return

        if tell_about_topic(command):
           return


        if "tell me about" in command or "who is" in command:
            tell_about_person(command)
            return

        if "play" in command and "spotify" in command:
            play_song_on_spotify(command)
            return

        if "exit" in command:
            self.add_text("[System] Exiting...")
            speak("Goodbye!")
            self.root.quit()
            return

        self.add_text("AI is thinking...")
        start_buffering()
        gemini_response = get_gemini_response(command)
        speak(gemini_response)
        self.add_text("AI: " + gemini_response)
  

def main():
    root = tk.Tk()
    app = AssistantGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
