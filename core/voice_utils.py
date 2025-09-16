import pyttsx3
import threading
from faster_whisper import WhisperModel
import torch
import sounddevice as sd
import soundfile as sf
import os

engine = pyttsx3.init()
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)

audio_lock = threading.Lock()

# Detect device
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"
print(f"🖥️ Faster-Whisper running on {device.upper()} ({compute_type})")

# Load Faster-Whisper once
whisper_model = WhisperModel("base", device=device, compute_type=compute_type)

def speak(text):
    with audio_lock:
        print("AI:", text)
        engine.say(text)
        engine.runAndWait()

def listen_command(duration=5):
    """
    Record microphone input for a short duration and transcribe with Faster-Whisper.
    """
    fs = 16000
    temp_filename = "temp_listen.wav"

    try:
        print("🎧 Listening...")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="float32")
        sd.wait()
        sf.write(temp_filename, recording, fs)

        segments, info = whisper_model.transcribe(temp_filename, beam_size=1)
        text = " ".join([seg.text for seg in segments]).strip().lower()
        print("You:", text)

        os.remove(temp_filename)
        return text
    except Exception as e:
        print(f"❌ Faster-Whisper listening error: {e}")
        return "error"
