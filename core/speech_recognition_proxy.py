import os
import sounddevice as sd
import soundfile as sf
import torch
from faster_whisper import WhisperModel
from core.text_to_speech import speak
from rapidfuzz import process, fuzz
import phonetics    

class WhisperSpeechRecognition:
    def __init__(self, model_name="base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "int8"  # works reliably offline
        print(f"🗣️ Initializing Faster-Whisper STT model: {model_name} on {self.device.upper()} ({self.compute_type})")
        self.model = WhisperModel(model_name, device=self.device, compute_type=self.compute_type)

        # List of names to detect
        self.common_names = [
            "vansh", "milap", "utkarsh", "shivansh", "yash", "aditya", "trace","call"
        ]

        # Precompute phonetic codes
        self.name_phonetic_map = {name: phonetics.dmetaphone(name)[0] for name in self.common_names}

        # Create an initial prompt for biasing the model toward names
        self.initial_prompt = "vansh milap utkarsh shivansh yash aditya hornet call"

    def correct_names(self, text):
        words = text.split()
        corrected = []

        for w in words:
            # Try exact fuzzy match first
            match, score, _ = process.extractOne(w, self.common_names, scorer=fuzz.ratio)
            if score > 85:
                corrected.append(match)
                continue

            # Try phonetic match
            w_phonetic = phonetics.dmetaphone(w)[0]
            best_match = w
            best_score = 0
            for name, code in self.name_phonetic_map.items():
                if code:
                    s = fuzz.ratio(w_phonetic, code)
                    if s > best_score:
                        best_score = s
                        best_match = name
            if best_score > 85:
                corrected.append(best_match)
            else:
                corrected.append(w)

        return " ".join(corrected)

    def recognize_audio(self, audio_file_path):
        try:
            segments, _ = self.model.transcribe(
                audio_file_path,
                beam_size=3,
                language="en",
                initial_prompt=self.initial_prompt  # bias Whisper toward names
            )
            text = " ".join([seg.text for seg in segments]).strip().lower()
            text = self.correct_names(text)
            print(f"[Faster-Whisper] Recognized: {text}")
            return text
        except Exception as e:
            print(f"[Faster-Whisper] Error: {e}")
            speak("Speech recognition error. Please try again.")
            return "error"

    def listen_with_microphone(self, phrase_time_limit=5):
        fs = 16000
        temp_wav = "temp_mic.wav"

        try:
            print("🎧 Listening...")
            recording = sd.rec(int(phrase_time_limit * fs), samplerate=fs, channels=1, dtype="float32")
            sd.wait()
            sf.write(temp_wav, recording, fs)

            text = self.recognize_audio(temp_wav)
            os.remove(temp_wav)
            return text
        except Exception as e:
            print(f"[Faster-Whisper] Microphone error: {e}")
            return "error"


# --- Global instance ---
proxy_aware_sr = WhisperSpeechRecognition()
