# core/enroll_voice.py

import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import noisereduce as nr
import torch
from speechbrain.inference.speaker import SpeakerRecognition
from core.voice_auth import is_vansh_speaking

verifier = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec"
)

def record_and_denoise(file_path, duration=4):
    fs = 16000
    print(f"\n🎙️ Recording → {file_path} ...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    clean = nr.reduce_noise(y=recording.flatten(), sr=fs)
    sf.write(file_path, clean, fs)
    print(f"✅ Saved: {file_path} ✔️")

def enroll_verified_live_voices(num_samples=500):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    folder = os.path.join(project_root, "voice_data")
    os.makedirs(folder, exist_ok=True)

    existing = [f for f in os.listdir(folder) if f.startswith("sample_") and f.endswith(".wav")]
    next_index = len(existing)

    added = 0
    attempts = 0

    while added < num_samples:
        filename = f"sample_{next_index + added}.wav"
        full_path = os.path.join(folder, filename)

        record_and_denoise(full_path, duration=4)
        result = is_vansh_speaking(full_path)
        if result == "match":
            print("✅ Voice verified as live and belonging to Vansh.")
            added += 1
        else:
            print("❌ Voice not accepted for training. Deleting...")
            os.remove(full_path)

        attempts += 1
        print(f"➡️ Progress: {added}/{num_samples} (Attempts: {attempts})")

    print(f"\n🎉 Collected {added} verified live samples.")
    update_embedding()

def update_embedding():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    folder = os.path.join(project_root, "voice_data")

    embeddings = []

    for file in sorted(os.listdir(folder), reverse=True):  # reverse order
        if file.endswith(".wav") and file.startswith("sample_"):
            try:
                path = os.path.join(folder, file).replace("\\", "/")
                signal = verifier.load_audio(path)
                signal = signal.unsqueeze(0)
                emb = verifier.encode_batch(signal).squeeze(0)
                embeddings.append(emb)
            except Exception as e:
                pass

    if embeddings:
        avg = torch.mean(torch.stack(embeddings), dim=0)
        out_path = os.path.join(folder, "vansh_embedding.pt")
        torch.save(avg, out_path)
        print(f"🧠 Embedding updated and saved to: {out_path}")
    else:
        print("❌ No valid embeddings found.")

if __name__ == "__main__":
    enroll_verified_live_voices(num_samples=500)
