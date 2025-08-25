import torch
from speechbrain.inference.speaker import SpeakerRecognition
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import noisereduce as nr
import librosa
import scipy.stats
import scipy.signal
from scipy.stats import skew
from core.utils import resource_path
import gc

verifier = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec"
)

def record_voice(filename="temp_voice.wav", duration=4):
    fs = 16000
    print("🎙️ Recording voice...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    clean_audio = nr.reduce_noise(y=recording.flatten(), sr=fs)
    print(f"🎚️ Max amplitude: {np.max(np.abs(recording))}")
    sf.write(filename, clean_audio, fs)
    print(f"📁 Voice recorded to {filename}")

def record_temp_voice(filename="temp_voice.wav", duration=3):
    fs = 16000
    print("AI: Verifying your voice...")
    print("🎙️ Recording voice...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    clean_audio = nr.reduce_noise(y=recording.flatten(), sr=fs)
    print(f"🎚️ Max amplitude: {np.max(np.abs(recording))}")
    sf.write(filename, clean_audio, fs)
    print(f"📁 Voice recorded to {filename}")

# 🛡️ Anti-replay detection (fully commented out – disabled for now)
def is_replay_attack(signal_np, sr=16000):
    return False

    # signal_np = signal_np / (np.max(np.abs(signal_np)) + 1e-9)

    # # MFCC & dynamics
    # mfcc = librosa.feature.mfcc(y=signal_np, sr=sr, n_mfcc=13)
    # mfcc_std = np.std(mfcc, axis=1).mean()
    # delta_std = np.std(librosa.feature.delta(mfcc))

    # # Attack profile
    # max_amp = np.max(np.abs(signal_np))
    # envelope = np.abs(signal_np)
    # attack_idx = np.argmax(envelope > 0.6 * max_amp)
    # attack_time = attack_idx / sr
    # attack_slope = max_amp / (attack_time + 1e-5)
    # ea_ratio = np.mean(signal_np**2) / (attack_time + 1e-5)

    # # Spectrum
    # stft = librosa.stft(signal_np, n_fft=1024, hop_length=256)
    # mag_spec = np.abs(stft)
    # phase_spec = np.angle(stft)
    # spectral_centroid = librosa.feature.spectral_centroid(S=mag_spec, sr=sr)
    # spectral_skewness = skew(spectral_centroid.flatten())

    # # Modulation spectrum
    # mod_spec = np.mean(np.abs(np.fft.fft(envelope))[:100])

    # # Pitch jitter
    # pitches, magnitudes = librosa.piptrack(y=signal_np, sr=sr)
    # pitch_track = np.mean(pitches[magnitudes > np.median(magnitudes)])
    # jitter = np.std(pitches[pitches > 0]) if np.any(pitches > 0) else 0

    # # Other features
    # high_freq_energy = np.mean(librosa.feature.spectral_bandwidth(y=signal_np, sr=sr)[0][-20:])
    # group_delay_proxy = np.std(phase_spec)
    # b, a = scipy.signal.butter(4, 40, btype='low', fs=sr)
    # pop_energy = np.sum(np.abs(scipy.signal.filtfilt(b, a, signal_np)))
    # am_variability = np.std(librosa.amplitude_to_db(mag_spec, ref=np.max))
    # noise_floor = np.mean(np.abs(signal_np[:int(sr * 0.3)]))

    # print(f"\n🧪 Anti-Replay Profile:")
    # print(f"   MFCC STD            : {mfcc_std:.4f}")
    # print(f"   Delta MFCC STD      : {delta_std:.4f}")
    # print(f"   Attack Slope        : {attack_slope:.2f}")
    # print(f"   High-Freq Energy    : {high_freq_energy:.4f}")
    # print(f"   Group Delay Proxy   : {group_delay_proxy:.4f}")
    # print(f"   Pop Energy (<40Hz)  : {pop_energy:.4f}")
    # print(f"   AM Variability      : {am_variability:.4f}")
    # print(f"   Energy-Attack Ratio : {ea_ratio:.6f}")
    # print(f"   Modulation Spectrum : {mod_spec:.4f}")
    # print(f"   Spectral Skewness   : {spectral_skewness:.4f}")
    # print(f"   Pitch Jitter        : {jitter:.4f}")
    # print(f"   Noise Floor         : {noise_floor:.6f}")

    # suspicious_flags = 0
    # if mfcc_std < 26.0: suspicious_flags += 1
    # if delta_std < 4.6: suspicious_flags += 1
    # if pop_energy < 15.0: suspicious_flags += 1
    # if am_variability < 12.0: suspicious_flags += 1
    # if mod_spec < 200.0: suspicious_flags += 1
    # if spectral_skewness < -1.5: suspicious_flags += 1

    # print(f"🔎 Total suspicious flags: {suspicious_flags}")

    # if suspicious_flags >= 6:
    #     print("🚫 Result: Detected playback (recorded) voice.\n")
    #     return True
    # else:
    #     print("✅ Result: Likely live voice.\n")
    #     return False

def is_vansh_speaking(temp_recorded_path="temp_voice.wav", threshold=0.30):
    enrolled_path = resource_path("voice_data/vansh_embedding.pt")

    if not os.path.exists(enrolled_path):
        print("❌ Enrollment embedding not found at", enrolled_path)
        return "no-match"

    try:
        signal = verifier.load_audio(temp_recorded_path)

        if signal.shape[-1] < 51200:
            print("⚠️ Voice too short for reliable speaker verification.")
            return "too-short"

        signal_np = signal.squeeze().numpy()

        # 🔇 Anti-replay temporarily disabled
        # if is_replay_attack(signal_np):
        #     print("❌ Detected playback (recorded) voice. Rejected.")
        #     return "replay"

        signal = signal.unsqueeze(0)
        user_emb = verifier.encode_batch(signal).squeeze(0)
        enrolled_emb = torch.load(enrolled_path)

        score = torch.nn.functional.cosine_similarity(
            user_emb.flatten(), enrolled_emb.flatten(), dim=0).item()

        print(f"🔍 Speaker verification score: {score:.3f}")
        return "match" if score > threshold else "no-match"

    except Exception as e:
        print("❌ Error in voice check:", e)
        return "no-match"

def cleanup_temp_voice(path="temp_voice.wav"):
    try:
        if os.path.exists(path) and "sample_" not in path and "voice_data" not in path:
            try:
                os.remove(path)
                print("🧽 Temp voice cleaned.")
            except PermissionError:
                print("⚠️ File in use, forcing cleanup...")
                gc.collect()
                try:
                    os.remove(path)
                    print("🧽 Cleaned after GC.")
                except Exception as e:
                    print(f"❌ Final delete failed: {e}")
    except Exception as e:
        print("Error during cleanup:", e)
