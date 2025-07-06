import os
import wave
import numpy as np
import librosa
import subprocess
import soundfile as sf
from scipy import signal

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

def analyze_spectral_content(sig, sr=44100, window_size=2048):
    """Analyze spectral content to detect bandwidth issues"""
    # Compute STFT
    f, t, Zxx = signal.stft(sig, fs=sr, nperseg=window_size)
    
    # Compute spectral centroid over time
    magnitude = np.abs(Zxx)
    spectral_centroid = np.sum(f[:, np.newaxis] * magnitude, axis=0) / np.sum(magnitude, axis=0)
    
    # Compute spectral rolloff (95% of energy)
    cumulative_energy = np.cumsum(magnitude, axis=0)
    total_energy = cumulative_energy[-1, :]
    rolloff_threshold = 0.95 * total_energy
    
    spectral_rolloff = np.zeros_like(spectral_centroid)
    for i in range(len(spectral_rolloff)):
        idx = np.where(cumulative_energy[:, i] >= rolloff_threshold[i])[0]
        if len(idx) > 0:
            spectral_rolloff[i] = f[idx[0]]
    
    return {
        'spectral_centroid': spectral_centroid,
        'spectral_rolloff': spectral_rolloff,
        'frequencies': f,
        'times': t,
        'magnitude': magnitude
    }

def detect_sample_rate_mismatch(sig1, sig2, sr=44100):
    """Detect if signals have different effective sample rates"""
    spec1 = analyze_spectral_content(sig1, sr)
    spec2 = analyze_spectral_content(sig2, sr)
    
    # Compare median spectral characteristics
    centroid1_median = np.median(spec1['spectral_centroid'])
    centroid2_median = np.median(spec2['spectral_centroid'])
    
    rolloff1_median = np.median(spec1['spectral_rolloff'])
    rolloff2_median = np.median(spec2['spectral_rolloff'])
    
    # Calculate ratios
    centroid_ratio = centroid2_median / centroid1_median if centroid1_median > 0 else 1.0
    rolloff_ratio = rolloff2_median / rolloff1_median if rolloff1_median > 0 else 1.0
    
    print(f"🔍 Spectral Analysis:")
    print(f"   Centroid ratio: {centroid_ratio:.3f}")
    print(f"   Rolloff ratio: {rolloff_ratio:.3f}")
    
    # If ratios are significantly different from 1, there might be a sample rate issue
    if abs(centroid_ratio - 1.0) > 0.1 or abs(rolloff_ratio - 1.0) > 0.1:
        print("⚠️ Potential sample rate mismatch detected!")
        return centroid_ratio, rolloff_ratio
    
    return 1.0, 1.0

def correct_sample_rate_mismatch(sig, correction_factor, sr=44100):
    """Correct sample rate mismatch by resampling"""
    if abs(correction_factor - 1.0) < 0.01:
        return sig
    
    # Calculate new sample rate
    new_sr = int(sr * correction_factor)
    print(f"🔧 Correcting sample rate: {sr} -> {new_sr}")
    
    # Resample
    corrected_sig = librosa.resample(sig, orig_sr=sr, target_sr=new_sr)
    # Resample back to original rate with correct timing
    corrected_sig = librosa.resample(corrected_sig, orig_sr=new_sr, target_sr=sr)
    
    return corrected_sig

def align_signals_spectral(sig1, sig2, sr=44100, max_lag_seconds=5):
    """
    Align signals using spectral features for better bandwidth matching
    """
    max_lag_samples = int(max_lag_seconds * sr)
    
    # Extract spectral features for alignment
    spec1 = analyze_spectral_content(sig1, sr)
    spec2 = analyze_spectral_content(sig2, sr)
    
    # Use spectral centroid as alignment feature
    centroid1 = spec1['spectral_centroid']
    centroid2 = spec2['spectral_centroid']
    
    # Smooth the centroids to reduce noise
    if len(centroid1) > 10:
        centroid1 = signal.savgol_filter(centroid1, min(21, len(centroid1)//2*2+1), 3)
    if len(centroid2) > 10:
        centroid2 = signal.savgol_filter(centroid2, min(21, len(centroid2)//2*2+1), 3)
    
    # Find alignment using spectral centroids
    if len(centroid1) > 0 and len(centroid2) > 0:
        # Resample centroids to match time scales
        time_scale = len(sig1) / len(centroid1)
        
        # Cross-correlate spectral centroids
        correlation = signal.correlate(centroid2, centroid1, mode='full')
        lags = signal.correlation_lags(len(centroid2), len(centroid1), mode='full')
        
        # Convert lag from spectral time to samples
        lags_samples = (lags * time_scale).astype(int)
        
        # Limit search range
        valid_indices = np.abs(lags_samples) <= max_lag_samples
        if np.any(valid_indices):
            correlation = correlation[valid_indices]
            lags_samples = lags_samples[valid_indices]
            
            # Find best alignment
            max_corr_idx = np.argmax(correlation)
            lag = lags_samples[max_corr_idx]
            
            print(f"🎯 Spectral alignment lag: {lag} samples ({lag/sr:.3f}s)")
            
            # Apply alignment
            if lag > 0:
                aligned_sig1 = sig1[lag:]
                aligned_sig2 = sig2
            elif lag < 0:
                aligned_sig1 = sig1
                aligned_sig2 = sig2[-lag:]
            else:
                aligned_sig1 = sig1
                aligned_sig2 = sig2
            
            # Trim to same length
            min_len = min(len(aligned_sig1), len(aligned_sig2))
            aligned_sig1 = aligned_sig1[:min_len]
            aligned_sig2 = aligned_sig2[:min_len]
            
            return aligned_sig1, aligned_sig2, lag
    
    # Fallback to original method
    return align_signals(sig1, sig2, max_lag_samples)

def align_signals_robust_v2(sig1, sig2, sr=44100, max_lag_seconds=5):
    """
    Enhanced robust alignment with bandwidth synchronization
    """
    print(f"🔍 Starting robust alignment v2...")
    
    # Step 1: Check for sample rate mismatches
    centroid_ratio, rolloff_ratio = detect_sample_rate_mismatch(sig1, sig2, sr)
    
    # Step 2: Correct sample rate if needed
    corrected_sig1 = sig1
    corrected_sig2 = sig2
    
    if abs(centroid_ratio - 1.0) > 0.05:
        print(f"🔧 Correcting sig2 sample rate by factor {1/centroid_ratio:.3f}")
        corrected_sig2 = correct_sample_rate_mismatch(sig2, 1/centroid_ratio, sr)
    
    # Step 3: Multiple alignment methods
    methods = []
    
    # Method 1: Direct cross-correlation
    try:
        aligned1, aligned2, lag1 = align_signals(corrected_sig1, corrected_sig2, int(max_lag_seconds * sr))
        corr1 = np.corrcoef(aligned1, aligned2)[0, 1] if len(aligned1) > 0 else -1
        methods.append(('direct', aligned1, aligned2, lag1, corr1))
    except Exception as e:
        print(f"⚠️ Direct method failed: {e}")
    
    # Method 2: Envelope-based alignment
    try:
        env1 = np.abs(signal.hilbert(corrected_sig1))
        env2 = np.abs(signal.hilbert(corrected_sig2))
        aligned_env1, aligned_env2, lag2 = align_signals(env1, env2, int(max_lag_seconds * sr))
        
        # Apply lag to original signals
        if lag2 > 0:
            test_sig1 = corrected_sig1[lag2:]
            test_sig2 = corrected_sig2
        elif lag2 < 0:
            test_sig1 = corrected_sig1
            test_sig2 = corrected_sig2[-lag2:]
        else:
            test_sig1 = corrected_sig1
            test_sig2 = corrected_sig2
        
        min_len = min(len(test_sig1), len(test_sig2))
        test_sig1 = test_sig1[:min_len]
        test_sig2 = test_sig2[:min_len]
        
        corr2 = np.corrcoef(test_sig1, test_sig2)[0, 1] if len(test_sig1) > 0 else -1
        methods.append(('envelope', test_sig1, test_sig2, lag2, corr2))
    except Exception as e:
        print(f"⚠️ Envelope method failed: {e}")
    
    # Method 3: Spectral alignment
    try:
        aligned1, aligned2, lag3 = align_signals_spectral(corrected_sig1, corrected_sig2, sr, max_lag_seconds)
        corr3 = np.corrcoef(aligned1, aligned2)[0, 1] if len(aligned1) > 0 else -1
        methods.append(('spectral', aligned1, aligned2, lag3, corr3))
    except Exception as e:
        print(f"⚠️ Spectral method failed: {e}")
    
    # Step 4: Choose best method
    if not methods:
        print("❌ All alignment methods failed!")
        return corrected_sig1, corrected_sig2, 0
    
    # Select method with highest correlation
    best_method = max(methods, key=lambda x: x[4] if not np.isnan(x[4]) else -1)
    method_name, best_aligned1, best_aligned2, best_lag, best_corr = best_method
    
    print(f"🎯 Best method: {method_name} (correlation: {best_corr:.3f})")
    
    # Step 5: Final bandwidth verification
    if len(best_aligned1) > sr and len(best_aligned2) > sr:  # Only if signals are long enough
        final_centroid_ratio, final_rolloff_ratio = detect_sample_rate_mismatch(best_aligned1, best_aligned2, sr)
        if abs(final_centroid_ratio - 1.0) > 0.1:
            print(f"⚠️ Warning: Bandwidth still mismatched after alignment (ratio: {final_centroid_ratio:.3f})")
    
    return best_aligned1, best_aligned2, best_lag

def align_signals(sig1, sig2, max_lag=None):
    """
    Improved version of the original align_signals function
    """
    print(f"🔍 Aligning signals: sig1={len(sig1)}, sig2={len(sig2)}")
    
    # Handle edge cases
    if len(sig1) == 0 or len(sig2) == 0:
        print("⚠️ Warning: One or both signals are empty")
        return np.array([]), np.array([]), 0
    
    # For small length differences, skip alignment
    if abs(len(sig1) - len(sig2)) <= 1:
        min_len = min(len(sig1), len(sig2))
        print(f"✅ Aligned lengths: sig1={min_len}, sig2={min_len}")
        return sig1[:min_len], sig2[:min_len], 0
    
    # Normalize signals more carefully
    def safe_normalize(sig):
        sig_mean = np.mean(sig)
        sig_std = np.std(sig)
        if sig_std < 1e-10:
            return sig - sig_mean
        return (sig - sig_mean) / sig_std
    
    sig1_norm = safe_normalize(sig1)
    sig2_norm = safe_normalize(sig2)
    
    # For very long signals, use multiple segments for more robust alignment
    if len(sig1) > 100000 or len(sig2) > 100000:
        # Use multiple segments and average the results
        seg_len = min(50000, len(sig1), len(sig2))
        segments = 3
        lags = []
        
        for i in range(segments):
            start1 = i * (len(sig1) - seg_len) // (segments - 1) if segments > 1 else (len(sig1) - seg_len) // 2
            start2 = i * (len(sig2) - seg_len) // (segments - 1) if segments > 1 else (len(sig2) - seg_len) // 2
            
            seg1 = sig1_norm[start1:start1 + seg_len]
            seg2 = sig2_norm[start2:start2 + seg_len]
            
            # Compute cross-correlation for this segment
            correlation = signal.correlate(seg2, seg1, mode='full')
            lags_seg = signal.correlation_lags(len(seg2), len(seg1), mode='full')
            
            # Find best lag for this segment
            if max_lag is not None:
                valid_indices = np.abs(lags_seg) <= max_lag
                if np.any(valid_indices):
                    correlation = correlation[valid_indices]
                    lags_seg = lags_seg[valid_indices]
            
            if len(correlation) > 0:
                max_corr_idx = np.argmax(correlation)
                lags.append(lags_seg[max_corr_idx])
        
        # Use median lag for robustness
        if lags:
            lag = int(np.median(lags))
        else:
            lag = 0
    else:
        # Original method for shorter signals
        correlation = signal.correlate(sig2_norm, sig1_norm, mode='full')
        lags = signal.correlation_lags(len(sig2_norm), len(sig1_norm), mode='full')
        
        if max_lag is not None:
            valid_indices = np.abs(lags) <= max_lag
            if np.any(valid_indices):
                correlation = correlation[valid_indices]
                lags = lags[valid_indices]
        
        if len(correlation) == 0:
            print("⚠️ Warning: No valid correlation found")
            return sig1, sig2, 0
        
        max_corr_idx = np.argmax(correlation)
        lag = lags[max_corr_idx]
    
    print(f"🎯 Computed lag: {lag}")
    
    # Apply the lag to align the original signals
    if lag > 0:
        aligned_sig1 = sig1[lag:]
        aligned_sig2 = sig2
    elif lag < 0:
        aligned_sig1 = sig1
        aligned_sig2 = sig2[-lag:]
    else:
        aligned_sig1 = sig1
        aligned_sig2 = sig2
    
    # Trim to same length
    min_len = min(len(aligned_sig1), len(aligned_sig2))
    aligned_sig1 = aligned_sig1[:min_len]
    aligned_sig2 = aligned_sig2[:min_len]
    
    print(f"✅ Aligned lengths: sig1={len(aligned_sig1)}, sig2={len(aligned_sig2)}")
    
    return aligned_sig1, aligned_sig2, lag

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



# Example usage
if __name__ == "__main__":
    # Load your audio files
    sr1, sig1 = load_audio("audio1.wav")
    sr2, sig2 = load_audio("audio2.wav")
    
    # Use the improved alignment
    aligned1, aligned2, lag = align_signals_robust_v2(sig1, sig2, sr1)
    
    # Save aligned audio
    sf.write("aligned_audio1.wav", aligned1, sr1)
    sf.write("aligned_audio2.wav", aligned2, sr1)