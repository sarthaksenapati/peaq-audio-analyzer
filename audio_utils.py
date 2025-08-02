## audio_utils.py
import os
import wave
import numpy as np
import librosa
import subprocess
import soundfile as sf


from pydub import AudioSegment

def get_audio_duration(file):
    """
    Get duration of any audio file (wav, mp3, m4a, aac, flac, etc.)
    Requires FFmpeg to be installed and available in PATH.
    """
    audio = AudioSegment.from_file(file)
    return len(audio) / 1000.0  # Duration in seconds



def load_audio(path, target_sr=44100, mono=True):
    """Stable audio loader using librosa for resampling and normalization"""
    audio, sr = librosa.load(path, sr=target_sr, mono=mono)
    audio = audio.astype(np.float32)
    if np.max(np.abs(audio)) > 0:
        audio /= np.max(np.abs(audio))  # Normalize
    return sr, audio


def quick_quality_check(ref_path, test_path):
    """Quick quality check to identify major issues"""
    ref_sr, ref_audio = load_audio(ref_path)
    test_sr, test_audio = load_audio(test_path)

    min_len = min(len(ref_audio), len(test_audio))
    ref_audio = ref_audio[:min_len]
    test_audio = test_audio[:min_len]

    print(f"🔍 QUICK QUALITY CHECK")
    print(f"📊 Sample rates: Ref={ref_sr}Hz, Test={test_sr}Hz")

    ref_fft = np.fft.fft(ref_audio)
    test_fft = np.fft.fft(test_audio)
    freqs = np.fft.fftfreq(len(ref_audio), 1 / ref_sr)

    pos_freqs = freqs[:len(freqs)//2]
    ref_spectrum = np.abs(ref_fft[:len(ref_fft)//2])
    test_spectrum = np.abs(test_fft[:len(test_fft)//2])

    ref_db = 20 * np.log10(ref_spectrum + 1e-10)
    test_db = 20 * np.log10(test_spectrum + 1e-10)

    ref_bw_idx = np.where(ref_db > (np.max(ref_db) - 20))[0]
    test_bw_idx = np.where(test_db > (np.max(test_db) - 20))[0]

    ref_bw = pos_freqs[ref_bw_idx[-1]] if len(ref_bw_idx) > 0 else 0
    test_bw = pos_freqs[test_bw_idx[-1]] if len(test_bw_idx) > 0 else 0

    print(f"📡 Bandwidth: Ref={ref_bw:.0f}Hz, Test={test_bw:.0f}Hz")
    print(f"📉 Bandwidth loss: {ref_bw - test_bw:.0f}Hz")

    ref_rms = np.sqrt(np.mean(ref_audio**2))
    test_rms = np.sqrt(np.mean(test_audio**2))
    print(f"📊 RMS levels: Ref={ref_rms:.4f}, Test={test_rms:.4f}")
    print(f"📊 RMS ratio: {test_rms / ref_rms:.4f}")

    if ref_bw - test_bw > 2000:
        print("❌ MAJOR BANDWIDTH LOSS - Check recording format!")
    elif ref_bw - test_bw > 500:
        print("⚠️  Moderate bandwidth loss detected")
    else:
        print("✅ Bandwidth looks OK")

    if abs(test_rms / ref_rms - 1.0) > 0.2:
        print("❌ SIGNIFICANT LEVEL DIFFERENCE - Check recording levels!")

    return ref_bw - test_bw, test_rms / ref_rms

def align_signals_by_cross_correlation(sig1, sig2, original_sr=44100, downsample_sr=8000):
    """
    Efficient alignment using downsampled cross-correlation for lag estimation,
    but extracts aligned segments from original high-res signals.
    """
    # Step 1: Downsample for alignment
    sig1_ds = librosa.resample(sig1, orig_sr=original_sr, target_sr=downsample_sr)
    sig2_ds = librosa.resample(sig2, orig_sr=original_sr, target_sr=downsample_sr)

    # Step 2: Find lag
    corr = np.correlate(sig2_ds, sig1_ds, mode='full')
    lag_ds = np.argmax(corr) - len(sig1_ds) + 1
    lag_orig = int(round(lag_ds * (original_sr / downsample_sr)))

    print(f"⚡ Fast cross-correlation lag: {lag_ds} samples @ {downsample_sr}Hz → {lag_orig} samples @ 44.1kHz")

    # Step 3: Align original full-res signals
    if lag_orig > 0:
        sig2_aligned = sig2[lag_orig:]
        sig1_aligned = sig1[:len(sig2_aligned)]
    elif lag_orig < 0:
        sig1_aligned = sig1[-lag_orig:]
        sig2_aligned = sig2[:len(sig1_aligned)]
    else:
        sig1_aligned = sig1
        sig2_aligned = sig2

    # Step 4: Truncate to same length
    min_len = min(len(sig1_aligned), len(sig2_aligned))
    sig1_aligned = sig1_aligned[:min_len]
    sig2_aligned = sig2_aligned[:min_len]

    print(f"✅ Aligned signals length: {min_len} samples ({min_len/original_sr:.2f} sec)")

    return sig1_aligned, sig2_aligned, lag_orig


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
