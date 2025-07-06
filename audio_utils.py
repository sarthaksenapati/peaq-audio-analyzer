import os
import wave
import numpy as np
import librosa
import soundfile as sf
import subprocess


def get_audio_duration(file):
    """Get duration of a WAV file in seconds"""
    with wave.open(file, 'rb') as w:
        return w.getnframes() / float(w.getframerate())


def load_audio(path, target_sr=44100, mono=True):
    """Load audio using soundfile and resample with librosa if needed"""
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


def align_signals_by_cross_correlation(sig1, sig2):
    """Align two signals using cross-correlation and ensure equal length"""
    corr = np.correlate(sig2, sig1, mode='full')
    lag = np.argmax(corr) - len(sig1) + 1
    print(f"📏 Detected offset (lag): {lag} samples")

    if lag > 0:
        aligned_sig2 = sig2[lag:]
        aligned_sig1 = sig1[:len(aligned_sig2)]
    elif lag < 0:
        aligned_sig1 = sig1[-lag:]
        aligned_sig2 = sig2[:len(aligned_sig1)]
    else:
        aligned_sig1 = sig1
        aligned_sig2 = sig2

    # ✅ Ensure final trim to match lengths (this fixes the broadcasting error)
    min_len = min(len(aligned_sig1), len(aligned_sig2))
    aligned_sig1 = aligned_sig1[:min_len]
    aligned_sig2 = aligned_sig2[:min_len]

    print(f"✅ Final aligned length: {min_len} samples")
    return aligned_sig1, aligned_sig2, lag


def trim_audio_with_ffmpeg(input_path, output_path, start_sec, duration_sec):
    """Trim audio using FFmpeg with hard duration and start time"""
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