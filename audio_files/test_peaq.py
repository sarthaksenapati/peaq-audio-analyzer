import numpy as np
import librosa
import os
import matplotlib.pyplot as plt
from PEAQ import PEAQ  # Import the simplified PEAQ model
import wave

# Function to load and normalize an audio file
def load_audio(filename, target_sr=48000):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    # Load audio using librosa and resample to target_sr
    data, sr = librosa.load(filename, sr=target_sr, mono=True)
    data = data.astype(np.float32)
    
    # Normalize to -1.0 to 1.0 range
    if np.max(np.abs(data)) > 0:
        data /= np.max(np.abs(data))
    
    return sr, data

# Plot frame-wise analysis results
def plot_results(BWRef, BWTest, NMR_per_frame, odg_per_frame):
    frames = np.arange(len(BWRef))

    plt.figure(figsize=(16, 9))

    # Bandwidth per frame
    plt.subplot(3, 1, 1)
    plt.plot(frames, BWRef, label="Bandwidth Reference")
    plt.plot(frames, BWTest, label="Bandwidth Test")
    plt.ylabel("Bandwidth")
    plt.legend()
    plt.title("Bandwidth per Frame")

    # NMR per frame
    plt.subplot(3, 1, 2)
    plt.plot(frames, NMR_per_frame, label="NMR per Frame", color='orange')
    plt.ylabel("NMR")
    plt.legend()
    plt.title("NMR per Frame")

    # Pseudo ODG per frame
    plt.subplot(3, 1, 3)
    plt.plot(frames, odg_per_frame, label="Pseudo ODG per Frame", color='green')
    plt.ylabel("ODG")
    plt.xlabel("Frame")
    plt.legend()
    plt.title("Pseudo ODG per Frame (not true PEAQ ODG)")

    plt.tight_layout()
    plt.show()

# Main analysis function
def main():
    import sys

    if len(sys.argv) != 3:
        print("Usage: python test_peaq.py reference.wav test.wav")
        sys.exit(1)

    ref_file = sys.argv[1]
    test_file = sys.argv[2]
    print(f"Reference file: {ref_file}")
    print(f"Test file: {test_file}")

    # Load both audio files
    try:
        fs_ref, ref_signal = load_audio(ref_file)
        fs_test, test_signal = load_audio(test_file)
    except FileNotFoundError as e:
        print(e)
        return

    # Ensure both signals are of equal length
    minlen = min(len(ref_signal), len(test_signal))
    ref_signal = ref_signal[:minlen]
    test_signal = test_signal[:minlen]

    # Estimate frame count based on frame/hop settings
    frame_size = 1024
    hop_size = 512
    estimated_frames = 1 + (minlen - frame_size) // hop_size
    print(f"Estimated number of frames: {estimated_frames}")

    # Run the simplified PEAQ processing
    peaq = PEAQ(fs_ref)
    num_frames = peaq.process(ref_signal, test_signal)
    print(f"Actual number of frames processed: {num_frames}")

    # Bandwidth computation across frames
    BWRef, BWTest = peaq.computeBW(peaq.X2MatR, peaq.X2MatT)
    print(f"Bandwidth Reference (mean): {np.mean(BWRef):.2f}")
    print(f"Bandwidth Test (mean): {np.mean(BWTest):.2f}")

    # NMR (Noise-to-Mask Ratio) calculation: overall stats
    NMR_avg, NMR_max = peaq.computeNMR(peaq.EbNMatT, peaq.EhsR, peaq.EbNMatR)
    print(f"NMR Avg: {NMR_avg:.2f}")
    print(f"NMR Max: {NMR_max:.2f}")

    # Per-frame NMR calculation (averaged across bands)
    eps = 1e-12
    try:
        nmr_per_frame = 10 * np.log10((peaq.EbNMatT + eps) / (peaq.EhsR + eps))
        nmr_per_frame = np.mean(nmr_per_frame, axis=1)
    except Exception as e:
        print("Failed to calculate per-frame NMR:", e)
        nmr_per_frame = np.zeros_like(BWRef)

    # Pseudo ODG calculation per frame (heuristic version)
    def pseudo_odg(nmr, bwref, bwtest):
        return np.clip(8.0 * nmr - 0.2 * np.abs(bwref - bwtest), -4, 0)

    odg_per_frame = pseudo_odg(nmr_per_frame, BWRef, BWTest)

    # Added energy is a simple energy-based error term
    added_energy = np.mean(np.abs(test_signal - ref_signal))
    print(f"Added energy: {added_energy:.5f}")

    # Final ODG score (simplified model combining all features)
    odg = peaq.computeODG(NMR_avg, NMR_max, BWRef, BWTest, added_energy)
    print(f"ODG (Objective Difference Grade): {odg:.2f}")

    # Display visual analysis
    plot_results(BWRef, BWTest, nmr_per_frame, odg_per_frame)


# Entry point
if __name__ == "__main__":
    main()
