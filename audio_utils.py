## audio_utils.py
import os
import wave
import numpy as np
import librosa
import subprocess
import soundfile as sf
import shutil
import config

from pydub import AudioSegment

def validate_ffmpeg():
    """
    Validate FFmpeg availability and return the command to use
    """
    # First check if ffmpeg is in PATH
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    
    # If not in PATH, try to find it using the find_ffmpeg module
    try:
        from find_ffmpeg import find_ffmpeg_path
        ffmpeg_path = find_ffmpeg_path()
        if ffmpeg_path and os.path.isfile(ffmpeg_path):
            return ffmpeg_path
    except ImportError:
        pass
    
    # If still not found, raise an error
    raise RuntimeError(
        "❌ FFmpeg not found. Please:\n"
        "1. Install FFmpeg and add to PATH, or\n"
        "2. Place ffmpeg.exe in one of these directories:\n"
        "   - C:\\ffmpeg\\bin\n"
        "   - C:\\Program Files\\ffmpeg\\bin\n"
        "   - Your project directory"
    )

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

def align_signals_by_cross_correlation(sig1, sig2, original_sr=44100, downsample_sr=8000, use_alignment=True):
    """
    Efficient alignment using downsampled cross-correlation for lag estimation,
    but extracts aligned segments from original high-res signals.
    Set use_alignment=False to skip alignment and return original signals.
    """
    # Skip alignment if sample-level delay compensation is already applied
    if (hasattr(config, 'ENABLE_AUTO_DELAY_COMPENSATION') and 
        config.ENABLE_AUTO_DELAY_COMPENSATION):
        print("🔧 Sample-level delay compensation enabled - skipping cross-correlation alignment")
        use_alignment = False
    
    if not use_alignment:
        print("🚫 Alignment is turned OFF. Returning original signals.")
        min_len = min(len(sig1), len(sig2))
        return sig1[:min_len], sig2[:min_len], 0

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
    try:
        ffmpeg_cmd = validate_ffmpeg()
    except RuntimeError as e:
        print(str(e))
        return False
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result = subprocess.run([
        ffmpeg_cmd, "-y",
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

def convert_and_trim_audio_with_ffmpeg(input_path, output_path, start_sec=0, duration_sec=None):
    """
    Convert and trim audio using FFmpeg with robust format handling
    Handles ADPCM_MS, MP3, M4A, and other formats → standardized WAV output
    """
    try:
        ffmpeg_cmd = validate_ffmpeg()
    except RuntimeError as e:
        print(str(e))
        return False
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cmd = [
        ffmpeg_cmd, "-y",
        "-i", input_path,
        "-ss", str(start_sec),
    ]
    
    # Add duration if specified
    if duration_sec is not None:
        cmd.extend(["-t", str(duration_sec)])
    
    cmd.extend([
        "-vn",                    # No video
        "-acodec", "pcm_s16le",   # 16-bit PCM little-endian
        "-ar", "44100",           # Standardize to 44.1kHz
        "-ac", "2",               # Force stereo
        "-f", "wav",              # Force WAV container
        "-avoid_negative_ts", "make_zero",  # Handle timing issues
        output_path
    ])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ FFmpeg conversion failed for {input_path}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
        return False
    
    print(f"✅ Converted: {os.path.basename(input_path)} → {os.path.basename(output_path)}")
    return True

def trim_test_audio_with_delay_compensation(input_path, output_path, start_sec=0, duration_sec=None, is_test_file=False):
    """
    Trim audio with automatic delay compensation for test files
    Automatically trims 9ms from test files to align with reference
    """
    try:
        ffmpeg_cmd = validate_ffmpeg()
    except RuntimeError as e:
        print(str(e))
        return False
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Calculate actual start time with delay compensation
    actual_start = start_sec
    if (is_test_file and 
        hasattr(config, 'ENABLE_AUTO_DELAY_COMPENSATION') and 
        config.ENABLE_AUTO_DELAY_COMPENSATION and
        hasattr(config, 'TEST_AUDIO_START_DELAY')):
        actual_start += config.TEST_AUDIO_START_DELAY
        print(f"🔧 Applying {config.TEST_AUDIO_START_DELAY*1000:.1f}ms delay compensation to test file")
    
    cmd = [
        ffmpeg_cmd, "-y",
        "-ss", str(actual_start),  # Start with delay compensation
    ]
    
    # Add duration if specified
    if duration_sec is not None:
        cmd.extend(["-t", str(duration_sec)])
    
    cmd.extend([
        "-i", input_path,
        "-vn",                    # No video
        "-acodec", "pcm_s16le",   # 16-bit PCM little-endian
        "-ar", "44100",           # Standardize to 44.1kHz
        "-ac", "2",               # Force stereo
        "-f", "wav",              # Force WAV container
        "-avoid_negative_ts", "make_zero",  # Handle timing issues
        output_path
    ])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ FFmpeg processing failed for {input_path}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
        return False
    
    delay_info = f" (with {config.TEST_AUDIO_START_DELAY*1000:.1f}ms compensation)" if is_test_file and config.ENABLE_AUTO_DELAY_COMPENSATION else ""
    print(f"✅ Processed: {os.path.basename(input_path)} → {os.path.basename(output_path)}{delay_info}")
    return True

def process_audio_pair_with_compensation(ref_path, test_path, ref_output=None, test_output=None):
    """
    Process reference and test audio files with automatic delay compensation
    """
    if ref_output is None:
        ref_output = ref_path.replace('.wav', '_processed.wav')
    if test_output is None:
        test_output = test_path.replace('.wav', '_processed.wav')
    
    print(f"\n🔄 Processing audio pair with delay compensation:")
    print(f"📁 Reference: {ref_path}")
    print(f"📁 Test: {test_path}")
    
    # Process reference file normally
    ref_success = trim_test_audio_with_delay_compensation(
        ref_path, ref_output, is_test_file=False
    )
    
    # Process test file with delay compensation
    test_success = trim_test_audio_with_delay_compensation(
        test_path, test_output, is_test_file=True
    )
    
    if ref_success and test_success:
        print(f"✅ Both files processed successfully")
        return ref_output, test_output
    else:
        print(f"❌ Processing failed")
        return None, None