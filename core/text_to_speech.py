import pyttsx3
import threading
import subprocess

def _speak_worker(text: str):
    """Internal function to handle the blocking TTS call in a separate thread."""
    print("AI:", text)
    try:
        # PowerShell/SAPI method is a robust fallback for Windows
        escaped_text = text.replace('"', '`"').replace("'", "`'")
        cmd = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak([Console]::InputEncoding.GetString([System.Text.Encoding]::Default.GetBytes("{escaped_text}")))'
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"❌ SAPI TTS Error: {e}. Falling back to pyttsx3.")
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e2:
            print(f"❌ pyttsx3 TTS Fallback Error: {e2}")

def speak(text: str):
    """
    Speaks the given text in a separate thread to avoid blocking the main application.
    """
    tts_thread = threading.Thread(target=_speak_worker, args=(text,), daemon=True)
    tts_thread.start()