import sounddevice as sd
import soundfile as sf
import numpy as np
import noisereduce as nr
import time
import os
import shutil
import threading

from core.utils import resource_path
from core.text_to_speech import speak
from core.voice_auth import is_vansh_speaking
from core.enroll_voice import update_embedding

def should_update_embedding(counter_file, threshold=10):
    if not os.path.exists(counter_file):
        with open(counter_file, "w") as f:
            f.write("1")
        return False

    with open(counter_file, "r") as f:
        count = int(f.read().strip())

    count += 1
    if count >= threshold:
        with open(counter_file, "w") as f:
            f.write("0")
        return True
    else:
        with open(counter_file, "w") as f:
            f.write(str(count))
        return False

def record_voice_dynamic(timeout=10, preserve_temp=False):
    fs = 44100
    threshold = 300
    silence_limit = 3.0

    print("🎙️ Adjusting for ambient noise...")
    time.sleep(1)
    print("🎙️ Speak now...")

    silence_chunks = 0
    max_silence_chunks = int(silence_limit * 10)
    started = False
    frames = []
    pre_voice_buffer = []
    pre_voice_max_chunks = 8

    def callback(indata, frames_count, time_info, status):
        nonlocal started, silence_chunks, frames, pre_voice_buffer
        amplitude = np.max(np.abs(indata))

        if not started:
            pre_voice_buffer.append(indata.copy())
            if len(pre_voice_buffer) > pre_voice_max_chunks:
                pre_voice_buffer.pop(0)

        if amplitude > threshold:
            if not started:
                frames.extend(pre_voice_buffer)
                started = True
            silence_chunks = 0
            frames.append(indata.copy())
        elif started:
            silence_chunks += 1
            frames.append(indata.copy())

    with sd.InputStream(samplerate=fs, channels=1, dtype='int16',
                        callback=callback, blocksize=int(fs / 10)):
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                print("⏱️ Timeout reached.")
                break
            if started and silence_chunks >= max_silence_chunks:
                print("🔇 Silence detected. Stopping.")
                break
            time.sleep(0.1)

    if not frames:
        print("📉 No voice detected.")
        return False, None, None

    audio = np.concatenate(frames).flatten()

    if np.max(np.abs(audio)) < 1000:
        print("📉 Voice too quiet. Try speaking louder.")
        speak("Your voice was too quiet. Please try again.")
        return False, None, None

    temp_path = "temp_voice.wav"
    sf.write(temp_path, audio, fs)
    print(f"📁 Voice recorded to {temp_path}")
    print(f"🎚️ Max amplitude: {np.max(np.abs(audio))}")

    try:
        sf.read(temp_path)
    except:
        pass

    result = is_vansh_speaking(temp_path)

    if result == "match":
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        folder = os.path.join(project_root, "voice_data")

        os.makedirs(folder, exist_ok=True)
        existing = [f for f in os.listdir(folder) if f.startswith("sample_") and f.endswith(".wav")]
        indices = [int(f.split("_")[1].split(".")[0]) for f in existing]
        next_index = max(indices) + 1 if indices else 1
        new_filename = f"sample_{next_index}.wav"
        final_path = os.path.join(folder, new_filename)

        if preserve_temp:
            shutil.copy(temp_path, final_path)
        else:
            shutil.move(temp_path, final_path)

        print(f"✅ Verified voice saved as → {final_path}")

        # Silent background embedding update every 10 samples
        counter_file = os.path.join(folder, "embedding_update_counter.txt")
        if should_update_embedding(counter_file):
            threading.Thread(target=update_embedding, name="VoiceEmbeddingUpdater", daemon=True).start()

        return True, (temp_path if preserve_temp else final_path), result

    else:
        print("⚠️ Voice not verified. Keeping as temp.")
        speak("Sorry, only Vansh can access me.")
        return True, temp_path, result
