# core/Hornet.py

# --- IMPORTS ---
import tkinter as tk
from tkinter import PhotoImage, Text, END, DISABLED, NORMAL
from PIL import Image, ImageTk, ImageSequence
import threading
import time
import os
import sys
import datetime
import struct

# --- CORE MODULES ---
from core.text_to_speech import speak
from core.voice_auth import is_vansh_speaking
from core.command_handler import CommandHandler
from core.enroll_voice import update_embedding
from core.speech_recognition_proxy import proxy_aware_sr

# --- UTILITIES ---
import pvporcupine
import pyaudio
import numpy as np
from scipy.io import wavfile

# ==============================================================================
#  UNIFIED VOICE CAPTURE FUNCTION
# ==============================================================================
# This function no longer records. It just receives audio data and processes it.
def listen_verify_and_transcribe(audio_data, fs=16000):
    print("🎙️ Verifying and transcribing captured audio...")

    if audio_data is None or len(audio_data) < fs / 2: # Check for short audio
        print("📉 Audio too short or empty.")
        return None, "no-voice"


    match_status = is_vansh_speaking(audio_data, sr=fs)

    if match_status != "match":
        return None, match_status

    print(f"✅ Verified voice.")

    # Save a temporary file for the speech recognition service
    temp_wav_path = os.path.join(os.path.dirname(__file__), "temp_command.wav")
    wavfile.write(temp_wav_path, fs, (audio_data * 32767).astype(np.int16)) # Convert float to int16 for saving
    
    print("🎤 Transcribing command...")
    command = proxy_aware_sr.recognize_audio(temp_wav_path)
    os.remove(temp_wav_path)
    
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
        self.command_handler = CommandHandler(self) # CommandHandler is now loaded normally
        
        # --- PICOVOICE PORCUPINE SETUP ---
        try:
            PICOVOICE_ACCESS_KEY = "DNblK3K6UO/hD+TWI1eKZg+h45gg+022eQay6D/G2nkjf/txR052YA=="
            model_file_name = None
            for f in os.listdir(self.resource_path("assets")):
                if f.startswith("Hornet") and f.endswith(".ppn"):
                    model_file_name = f
                    break
            
            if not model_file_name:
                raise FileNotFoundError("Could not find the Hornet .ppn model file in the assets folder.")

            keyword_path = self.resource_path(os.path.join("assets", model_file_name))

            self.porcupine = pvporcupine.create(
                access_key=PICOVOICE_ACCESS_KEY,
                keyword_paths=[keyword_path]
            )
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            print("✅ PicoVoice Porcupine engine initialized for 'Hornet'.")
        except Exception as e:
            print(f"❌ Error initializing Porcupine: {e}")
            self.porcupine = None
        # --- END OF SETUP ---

        self.ui_initialized = False
        self.setup_ui()
        
        if self.ui_initialized:
            threading.Thread(target=self.time_based_greeting, daemon=True).start()
            if self.porcupine:
                self.start_wake_word_listener()
            else:
                 self.add_text("[FATAL ERROR] Wake Word Engine failed to start. Check Access Key or .ppn file.")
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
            self.add_text("[System] UI Initialized. Say 'Hornet'.")
            
            self.ui_initialized = True
        except Exception as e:
            print(f"❌ Error during UI setup: {e}")

    def animate(self):
        self.canvas.itemconfig(self.bg_image, image=self.frames[self.gif_index])
        self.gif_index = (self.gif_index + 1) % len(self.frames)
        self.root.after(100, self.animate)

    def start_wake_word_listener(self):
        def _listen_continuously():
            print("🎧 Listening for 'Hornet'...")
            while True:
                try:
                    pcm = self.audio_stream.read(self.porcupine.frame_length)
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                    keyword_index = self.porcupine.process(pcm)

                    if keyword_index >= 0:
                        print("🔔 Wake word 'Hornet' detected!")
                        self.add_text("[System] Wake word detected. Listening...")
                        self._record_and_process_command(pcm)
                        print("🎧 Listening for 'Hornet'...")

                except Exception as e:
                    print(f"Wake word listener error: {e}")
                    time.sleep(1)

        threading.Thread(target=_listen_continuously, daemon=True).start()

    def _record_and_process_command(self, first_chunk):
        recorded_frames = [first_chunk]
        silence_limit_sec = 1.5
        threshold = 500
        
        silence_frames = 0
        max_silence_frames = int(silence_limit_sec * self.porcupine.sample_rate / self.porcupine.frame_length)

        while True:
            pcm_chunk_raw = self.audio_stream.read(self.porcupine.frame_length)
            pcm_chunk = struct.unpack_from("h" * self.porcupine.frame_length, pcm_chunk_raw)
            recorded_frames.append(pcm_chunk)

            intensity = np.mean(np.abs(pcm_chunk))
            if intensity < threshold:
                silence_frames += 1
            else:
                silence_frames = 0

            if silence_frames > max_silence_frames:
                break
        
        print("✅ Command recording finished.")
        
        audio_data_int16 = np.hstack(recorded_frames)
        audio_data_float32 = audio_data_int16.astype(np.float32) / 32767.0
        
        command, status = listen_verify_and_transcribe(audio_data_float32)

        if status == "match":
            self.add_text("[Security] Voice Matched.")
            if self.command_handler and command and command != "network error":
                command_phrase = command.lower().replace("hornet", "").strip()
                if command_phrase:
                    self.add_text(f"You: {command_phrase}")
                    threading.Thread(target=lambda: self.command_handler.handle_text(command_phrase), daemon=True).start()
                else:
                    self.add_text("[System] No command followed wake word.")
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


