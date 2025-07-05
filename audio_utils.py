import os
import wave
import numpy as np
import librosa
import subprocess
import soundfile as sf

def get_audio_duration(file):
    with wave.open(file, 'rb') as w:
        return w.getnframes() / float(w.getframerate())

def load_audio(path, target_sr=44100, mono=True):
    audio, sr = sf.read(path)
    # Resample if needed
    if sr != target_sr:
        if audio.ndim == 1:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        else:
            audio = librosa.resample(audio.T, orig_sr=sr, target_sr=target_sr).T
        sr = target_sr
    # Convert to mono if requested
    if mono and audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    return sr, audio

def align_signals(sig1, sig2):

    if len(sig1) < 3 or len(sig2) < 3:
        return np.array([]), np.array([]), 0  # Empty signals safeguard

    # Cross-correlation
    corr = np.correlate(sig2, sig1, mode='full')
    lag = np.argmax(corr) - len(sig1) + 1

    if lag > 0:
        aligned_test = sig2[lag:]
        aligned_ref = sig1[:len(aligned_test)]
    elif lag < 0:
        aligned_ref = sig1[-lag:]
        aligned_test = sig2[:len(aligned_ref)]
    else:
        aligned_ref = sig1
        aligned_test = sig2

    # Final length match
    min_len = min(len(aligned_ref), len(aligned_test))
    return aligned_ref[:min_len], aligned_test[:min_len], lag

def trim_audio_with_ffmpeg(input_path, output_path, start_sec, duration_sec):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result = subprocess.run([
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-t", str(duration_sec),
        "-i", input_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        output_path
    ], capture_output=True)
    return result.returncode == 0
