from pydub.generators import Sine
from pydub import AudioSegment
import pyttsx3
import time
import os

def generate_intro_bass():
    intro = AudioSegment.silent(duration=300)
    for freq, duration in [(70, 200), (50, 300), (30, 400)]:
        sine = Sine(freq).to_audio_segment(duration=duration).apply_gain(+6)
        intro += sine.fade_out(150)
    return intro

def generate_tts_message(text="Welcome back, Vansh", path="tts_output.wav"):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    engine.setProperty('volume', 1.0)
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'Zira' in voice.name or 'female' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.save_to_file(text, path)
    engine.runAndWait()
    time.sleep(2)  # ensure file is written
    return AudioSegment.from_wav(path)

def generate_final_audio():
    intro = generate_intro_bass()
    tts = generate_tts_message()
    combined = intro + AudioSegment.silent(duration=300) + tts
    output_path = "futuristic_welcome_vansh.wav"
    combined.export(output_path, format="wav")
    print(f"✅ File saved as {output_path}")

generate_final_audio()

