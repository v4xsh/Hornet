import pyttsx3
import pygame
import threading
import time
import subprocess
import sys
from core.utils import resource_path

# ✅ Initialize TTS engine
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 180)      # Speed of speech
    engine.setProperty('volume', 1.0)    # Volume (0.0 to 1.0)
    
    # Print available voices for debugging
    voices = engine.getProperty('voices')
    print(f"🔊 TTS Engine initialized with {len(voices)} voices available")
    if voices:
        print(f"🔊 Using voice: {voices[0].name}")
except Exception as e:
    print(f"❌ TTS Engine initialization error: {e}")
    engine = None

# ✅ Lock for thread-safe audio operations
audio_lock = threading.Lock()

# ✅ Initialize pygame mixer
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# ✅ Buffering sound control
buffering = False
buffering_thread = None

# ✅ Alternative TTS using Windows SAPI
def speak_sapi(text):
    try:
        # Use Windows Speech API directly via PowerShell
        escaped_text = text.replace('"', '`"').replace("'", "`'")
        cmd = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak(\"{escaped_text}\")'
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        print("✅ SAPI TTS completed")
        return True
    except Exception as e:
        print(f"❌ SAPI TTS Error: {e}")
        return False

# ✅ Speak text aloud
def speak(text):
    print("AI:", text)
    
    # Try Windows SAPI first (more reliable with pygame)
    if speak_sapi(text):
        return
        
    if engine is None:
        print("❌ TTS Engine not available")
        return
        
    try:
        # Completely stop pygame mixer to avoid audio conflicts
        pygame.mixer.music.stop()
        pygame.mixer.stop()
        time.sleep(0.2)  # Give pygame more time to release audio
        
        # Use TTS without the lock first
        engine.say(text)
        engine.runAndWait()
        print("✅ TTS completed successfully")
        
    except Exception as e:
        print("❌ TTS Error:", e)
        # Fallback: try to reinitialize the engine
        try:
            if engine:
                engine.stop()
            new_engine = pyttsx3.init()
            new_engine.setProperty('rate', 180)
            new_engine.setProperty('volume', 1.0)
            new_engine.say(text)
            new_engine.runAndWait()
            print("✅ TTS fallback completed")
        except Exception as e2:
            print("❌ TTS Fallback Error:", e2)

# ✅ Play buffering sound (looped)
def play_buffering_sound():
    try:
        pygame.mixer.music.load(resource_path("assets/buffering.wav"))
        with audio_lock:
            pygame.mixer.music.play(-1)  # Loop infinitely

        while buffering:
            time.sleep(0.1)

    except Exception as e:
        print("❌ Buffering Sound Error:", e)

# ✅ Start buffering thread
def start_buffering():
    global buffering, buffering_thread
    if not buffering:
        buffering = True
        buffering_thread = threading.Thread(target=play_buffering_sound, daemon=True)
        buffering_thread.start()

# ✅ Stop buffering sound
def stop_buffering():
    global buffering
    buffering = False
    with audio_lock:
        pygame.mixer.music.stop()
    time.sleep(0.3)
