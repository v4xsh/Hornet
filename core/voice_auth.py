import torch
from speechbrain.inference.speaker import SpeakerRecognition
import os
import numpy as np
import time
import soundfile as sf
from core.utils import resource_path

# --- SETUP DEVICE (CUDA OR CPU) ---
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ VoiceAuth: Using device -> {device.upper()}")

# --- Load SpeechBrain model ---
verifier = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    run_opts={"device": device}
)

def is_vansh_speaking(audio_data: np.ndarray, sr: int, threshold=0.30):
    """
    Verifies the speaker from an in-memory audio array using the selected device.
    If verified, saves the attempt to voice_data with a timestamp.
    """
    enrolled_path = resource_path("voice_data/vansh_embedding.pt")

    if not os.path.exists(enrolled_path):
        print(f"❌ Enrollment embedding not found at {enrolled_path}")
        return "no-match"

    try:
        # Minimum audio length: 2 seconds at 16kHz = 32000 samples
        if len(audio_data) < 32000:
            print("⚠️ Voice too short for reliable speaker verification.")
            return "too-short"

        # Convert audio data to a tensor and move to the correct device
        signal = torch.from_numpy(audio_data).float().unsqueeze(0).to(device)

        # ✅ Safe load (future-proof, no performance impact)
        enrolled_emb = torch.load(enrolled_path, weights_only=True).to(device)

        # Perform high-speed verification
        user_emb = verifier.encode_batch(signal).squeeze(0)

        score = torch.nn.functional.cosine_similarity(
            user_emb.flatten(), enrolled_emb.flatten(), dim=0
        ).item()

        print(f"🔍 Speaker verification score: {score:.3f} (computed on {device.upper()})")

        if score > threshold:
            # Save verified attempt
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_path = resource_path(f"voice_data/verified_{timestamp}.wav")
            try:
                sf.write(save_path, audio_data, sr)
                print(f"💾 Saved verified audio to {save_path}")
            except Exception as e:
                print(f"⚠️ Could not save verified audio: {e}")
            return "match"
        else:
            return "no-match"

    except Exception as e:
        print(f"❌ Error in voice check: {e}")
        return "error"
