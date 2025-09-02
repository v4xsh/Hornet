import torch
from speechbrain.inference.speaker import SpeakerRecognition
import os
import numpy as np
from core.utils import resource_path

# --- SETUP DEVICE (CUDA OR CPU) ---
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ VoiceAuth: Using device -> {device.upper()}")

# --- NEW, SIMPLER APPROACH: LOAD MODEL DIRECTLY FROM SOURCE ---
# This lets SpeechBrain handle file management in its own cache,
# completely avoiding the local file permission errors on Windows.
verifier = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    run_opts={"device": device}
)

def is_vansh_speaking(audio_data: np.ndarray, sr: int, threshold=0.30):
    """
    Verifies the speaker from an in-memory audio array using the selected device.
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
        enrolled_emb = torch.load(enrolled_path).to(device)

        # Perform high-speed verification
        user_emb = verifier.encode_batch(signal).squeeze(0)

        score = torch.nn.functional.cosine_similarity(
            user_emb.flatten(), enrolled_emb.flatten(), dim=0
        ).item()

        print(f"🔍 Speaker verification score: {score:.3f} (computed on {device.upper()})")
        return "match" if score > threshold else "no-match"

    except Exception as e:
        print(f"❌ Error in voice check: {e}")
        return "error"