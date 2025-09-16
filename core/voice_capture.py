import torch
from faster_whisper import WhisperModel
import sounddevice as sd
import soundfile as sf
from core.text_to_speech import speak
import os
from rapidfuzz import process, fuzz

# Load Faster-Whisper once
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"

whisper_model = WhisperModel("base", device=device, compute_type=compute_type)

# List of common names to correct
common_names = ["vansh", "milap", "utkarsh", "shivansh", "yash", "aditya"]

def correct_names(text):
    """Fuzzy-match words against common names and correct probable matches"""
    words = text.split()
    corrected = []
    for w in words:
        match, score, _ = process.extractOne(w, common_names, scorer=fuzz.ratio)
        if score > 80:  # threshold for correction
            corrected.append(match)
        else:
            corrected.append(w)
    return " ".join(corrected)

def record_and_transcribe(prompt, duration=10):
    fs = 16000
    temp_filename = "temp_capture.wav"

    speak(prompt)
    print(f"🎙️ Recording for {duration} seconds...")

    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="float32")
        sd.wait()
        sf.write(temp_filename, recording, fs)
        print("🎤 Recording complete. Transcribing...")

        segments, info = whisper_model.transcribe(temp_filename, beam_size=1)
        text = " ".join([seg.text for seg in segments]).strip().lower()
        text = correct_names(text)  # apply offline name correction
        print(f"📝 Transcribed: {text}")

    except Exception as e:
        print(f"❌ Faster-Whisper error: {e}")
        speak("There was an error with speech recognition.")
        text = "error"
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return text

