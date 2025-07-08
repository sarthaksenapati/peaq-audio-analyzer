import numpy as np
import matplotlib.pyplot as plt
import os
import librosa
from PEAQ import PEAQ  # Assuming PEAQ.py is in the same folder or Python path

# Your plotting function, modified to save plots instead of showing
def plot_results(BWRef, BWTest, NMR_per_frame, odg_per_frame, output_path):
    frames = np.arange(len(BWRef))

    plt.figure(figsize=(16, 9))

    plt.subplot(3, 1, 1)
    plt.plot(frames, BWRef, label="Bandwidth Reference")
    plt.plot(frames, BWTest, label="Bandwidth Test")
    plt.ylabel("Bandwidth")
    plt.legend()
    plt.title("Bandwidth per Frame")

    plt.subplot(3, 1, 2)
    plt.plot(frames, NMR_per_frame, label="NMR per Frame", color='orange')
    plt.ylabel("NMR")
    plt.legend()
    plt.title("NMR per Frame")

    plt.subplot(3, 1, 3)
    plt.plot(frames, odg_per_frame, label="Pseudo ODG per Frame", color='green')
    plt.ylabel("ODG")
    plt.xlabel("Frame")
    plt.legend()
    plt.title("Pseudo ODG per Frame (not true PEAQ ODG)")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def process_file_pair(ref_file, test_file, output_file):
    fs = 48000

    # Load audio files
    ref_signal, _ = librosa.load(ref_file, sr=fs, mono=True)
    test_signal, _ = librosa.load(test_file, sr=fs, mono=True)

    # Truncate to equal length
    minlen = min(len(ref_signal), len(test_signal))
    ref_signal = ref_signal[:minlen]
    test_signal = test_signal[:minlen]

    # Initialize PEAQ and process
    peaq = PEAQ(fs)
    num_frames = peaq.process(ref_signal, test_signal)

    # Compute bandwidth per frame
    BWRef, BWTest = peaq.computeBW(peaq.X2MatR, peaq.X2MatT)

    # Compute NMR (Noise-to-Mask Ratio)
    with np.errstate(divide='ignore', invalid='ignore'):
        NMR = 10 * np.log10((peaq.EbNMatT + 1e-12) / (peaq.EhsR + 1e-12))

    # For plotting per-frame NMR, average over frame bands
    NMR_per_frame = np.mean(NMR, axis=1)

    # Compute ODG per frame (using simplified approach)
    odg_per_frame = np.zeros(num_frames)
    for i in range(num_frames):
        nmr_avg = np.mean(NMR[i, :])
        nmr_max = np.max(NMR[i, :])
        bw_ref_val = BWRef[i]
        bw_test_val = BWTest[i]
        added_energy = np.mean(np.abs(peaq.X2MatT[i, :] - peaq.X2MatR[i, :]))

        odg_per_frame[i] = peaq.computeODG(nmr_avg, nmr_max, 
                                           np.array([bw_ref_val]), 
                                           np.array([bw_test_val]), 
                                           added_energy)

    # Plot and save the graph
    plot_results(BWRef, BWTest, NMR_per_frame, odg_per_frame, output_file)
    print(f"Saved plot: {output_file}")


def main():
    ref_folder = r"."
    test_folder = r"."
    output_folder = r"C:\Users\KIIT\OneDrive\Desktop\graphs"

    os.makedirs(output_folder, exist_ok=True)

    for i in range(1, 31):
        ref_file = os.path.join(ref_folder, f"{i}.wav")
        test_file = os.path.join(test_folder, f"{i}_D.wav")
        output_file = os.path.join(output_folder, f"graph_{i}.png")

        if not os.path.exists(ref_file):
            print(f"Reference file not found: {ref_file}")
            continue
        if not os.path.exists(test_file):
            print(f"Test file not found: {test_file}")
            continue

        process_file_pair(ref_file, test_file, output_file)


if __name__ == "__main__":
    main()
