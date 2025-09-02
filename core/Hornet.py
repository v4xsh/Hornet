# core/Hornet.py

# --- IMPORTS ---
import tkinter as tk
from tkinter import PhotoImage, Scrollbar, Text, END, DISABLED, NORMAL
from PIL import Image, ImageTk, ImageSequence
import threading
import time
import os
import sys
import datetime

# --- CORE MODULES ---
from core.text_to_speech import speak
from core.voice_auth import is_vansh_speaking
from core.command_handler import CommandHandler
from core.enroll_voice import update_embedding
from core.speech_recognition_proxy import proxy_aware_sr 

# --- UTILITIES ---
import sounddevice as sd
import numpy as np
import soundfile as sf

# ==============================================================================
#  UNIFIED VOICE CAPTURE FUNCTION
# ==============================================================================

def listen_verify_and_transcribe(timeout=8):
    fs = 16000
    silence_limit_sec = 2.0
    threshold = 0.01

    print("🎙️  Listening for command...")
    recorded_frames = []
    is_speaking = False
    silence_frames = 0
    max_silence_frames = int(silence_limit_sec * fs / 1024)

    def callback(indata, frames, time, status):
        nonlocal is_speaking, silence_frames
        if np.linalg.norm(indata) > threshold:
            is_speaking = True
            silence_frames = 0
        elif is_speaking:
            silence_frames += 1
        if is_speaking:
            recorded_frames.append(indata.copy())

    stream = sd.InputStream(samplerate=fs, channels=1, dtype='float32', callback=callback)
    with stream:
        start_time = time.time()
        while time.time() - start_time < timeout:
            if is_speaking and silence_frames > max_silence_frames:
                break
            time.sleep(0.1)

    if not recorded_frames:
        print("📉 No voice detected.")
        return None, "no-voice"

    audio_data = np.concatenate(recorded_frames).flatten()
    match_status = is_vansh_speaking(audio_data, sr=fs)

    if match_status != "match":
        return None, match_status

    # ✅ --- START OF THE FIX ---
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) 
    folder = os.path.join(project_root, "voice_data")
    os.makedirs(folder, exist_ok=True)
    
    existing_samples = [f for f in os.listdir(folder) if f.startswith("sample_") and f.endswith(".wav")]
    
    if not existing_samples:
        next_index = 1
    else:
        # Find the highest number in the existing filenames and add 1
        indices = [int(f.split('_')[1].split('.')[0]) for f in existing_samples]
        next_index = max(indices) + 1
        
    final_path = os.path.join(folder, f"sample_{next_index}.wav")
    sf.write(final_path, audio_data, fs)
    # ✅ --- END OF THE FIX ---
    
    print(f"✅ Verified voice saved for training -> {final_path}")
    
    print("🎤 Transcribing command...")
    command = proxy_aware_sr.recognize_audio(final_path)
    
    return command, match_status

# ==============================================================================
#  GUI AND MAIN APP LOGIC
# ==============================================================================

class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hornet AI")
        self.root.geometry("800x700")
        self.root.configure(bg="black")
        self.root.resizable(False, False)
        self.root.wm_attributes("-topmost", True)
        self.command_handler = CommandHandler(self)
        
        self.ui_initialized = False
        self.setup_ui()
        
        if self.ui_initialized:
            self.root.bind("<F2>", lambda e: threading.Thread(target=self.run_voice_command, daemon=True).start())
            threading.Thread(target=self.time_based_greeting, daemon=True).start()
            self.start_wake_word_listener()
        else:
            print("❌ UI setup failed. Halting background thread initialization.")
            if hasattr(self, 'chat_log'):
                self.add_text("[FATAL ERROR] UI setup failed. Check asset paths.")

    def setup_ui(self):
        try:
            self.canvas = tk.Canvas(self.root, width=800, height=700, highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)

            gif_path = self.resource_path("assets/goku.gif")
            if not os.path.exists(gif_path):
                print(f"Error: GIF file not found at {gif_path}")
                self.canvas.create_text(400, 350, text=f"ERROR: Asset not found\n{gif_path}", fill="red", font=("Consolas", 14))
                return
            
            gif = Image.open(gif_path)
            frame_size = (800, 600)
            self.frames = [ImageTk.PhotoImage(img.resize(frame_size, Image.LANCZOS).convert('RGBA'))
                           for img in ImageSequence.Iterator(gif)]
            self.gif_index = 0
            self.bg_image = self.canvas.create_image(0, 0, anchor='nw', image=self.frames[0])
            self.animate()
            
            self.chat_log = Text(self.root, bg="#000000", fg="sky blue", font=("Consolas", 10), wrap='word', bd=0)
            self.chat_log.place(x=0, y=600, width=800, height=100)
            self.add_text("[System] UI Initialized. Type or say 'Hey Hornet'.")
            
            self.ui_initialized = True
        except Exception as e:
            print(f"❌ Error during UI setup: {e}")

    def animate(self):
        self.canvas.itemconfig(self.bg_image, image=self.frames[self.gif_index])
        self.gif_index = (self.gif_index + 1) % len(self.frames)
        self.root.after(100, self.animate)

    def start_wake_word_listener(self):
        def _listen_for_wake_word():
            while True:
                try:
                    trigger = proxy_aware_sr.listen_with_microphone(timeout=None, phrase_time_limit=3)
                    if trigger and ("hey hornet" in trigger or trigger.strip() == "hornet"):
                        print("🔔 Wake word detected")
                        self.add_text("[System] Wake word detected. Verifying...")
                        self.run_voice_command()
                except Exception as e:
                    print(f"Wake word listener error: {e}")
                    time.sleep(1)
        
        threading.Thread(target=_listen_for_wake_word, daemon=True).start()
        
    def run_voice_command(self):
        command, status = listen_verify_and_transcribe()

        if status == "match":
            # speak("Voice verified.")
            self.add_text("[Security] Voice Matched.")
            if command and command != "network error":
                self.add_text(f"You: {command}")
                threading.Thread(target=lambda: self.command_handler.handle_text(command), daemon=True).start()
            elif command == "network error":
                self.add_text("[Error] Could not connect to speech service.")
            else:
                self.add_text("[System] I didn't catch that.")
                speak("Sorry, I didn't catch that.")
        
        elif status in ["no-match", "too-short", "error"]:
            self.add_text(f"[Security] Unauthorized voice detected. Status: {status}")
            speak("Sorry, I can only be accessed by my creator.")

    def time_based_greeting(self):
        hour = datetime.datetime.now().hour
        greeting = "Hello Vansh!"
        if 5 <= hour < 12: greeting = "Good morning Vansh! How can I help you today?"
        elif 12 <= hour < 17: greeting = "Good afternoon Vansh, how are you doing?"
        elif 17 <= hour < 22: greeting = "Good evening Vansh! Need any assistance?"
        speak(greeting)
    
    def add_text(self, text):
        if hasattr(self, 'root'):
            self.root.after(0, self._update_chat_log, text)

    def _update_chat_log(self, text):
        if not hasattr(self, 'chat_log') or not self.root.winfo_exists(): return
        self.chat_log.config(state=tk.NORMAL)
        self.chat_log.insert(END, text + "\n")
        self.chat_log.config(state=tk.DISABLED)
        self.chat_log.see(END)
    
    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(base_path, relative_path)

# ==============================================================================
#  APPLICATION STARTUP
# ==============================================================================

def startup_embedding_update():
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        folder = os.path.join(project_root, "voice_data")
        embedding_path = os.path.join(folder, "vansh_embedding.pt")
        if not os.path.exists(embedding_path):
            print("Embedding not found, creating a new one...")
            threading.Thread(target=update_embedding, daemon=True).start()
            return
            
        emb_time = os.path.getmtime(embedding_path)
        wav_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".wav")]
        if wav_files and max(os.path.getmtime(p) for p in wav_files) > emb_time:
            print("🔄 Newer voice samples detected, updating embedding...")
            threading.Thread(target=update_embedding, daemon=True).start()
        else:
            print("✅ Voice embedding is up to date.")
    except Exception as e:
        print(f"Error checking embedding: {e}")
        
if __name__ == "__main__":
    startup_embedding_update()
    root = tk.Tk()
    app = AssistantGUI(root)
    root.mainloop()