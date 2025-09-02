# core/voice_capture.py

import sounddevice as sd
import numpy as np
import soundfile as sf
import speech_recognition as sr
import os
from core.text_to_speech import speak

def record_and_transcribe(prompt, duration=10):
    """
    A simple, self-contained function that speaks a prompt, records audio,
    transcribes it, cleans up, and returns the text.
    """
    fs = 16000  # Use a standard sample rate
    temp_filename = "temp_capture.wav"
    
    speak(prompt)
    print(f"🎙️ Recording for {duration} seconds...")
    
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
    sd.wait()  # Wait for the recording to finish
    
    sf.write(temp_filename, recording, fs)
    print("🎤 Recording complete. Transcribing...")

    # Transcribe the audio
    r = sr.Recognizer()
    text = ""
    try:
        with sr.AudioFile(temp_filename) as source:
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.record(source)
            text = r.recognize_google(audio).lower()
            print(f"📝 Transcribed: {text}")
    except sr.UnknownValueError:
        print("Could not understand audio.")
        speak("I didn't catch that.")
    except sr.RequestError as e:
        print(f"Speech recognition service error; {e}")
        speak("There was an error with the speech service.")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            
    return text