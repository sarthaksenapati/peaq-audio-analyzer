import numpy as np
import matplotlib.pyplot as plt
from PEAQ import PEAQ

import os

import numpy as np
import matplotlib.pyplot as plt
from PEAQ import PEAQ
from audio_utils import load_audio, align_signals


import os

def run_peaq_analysis(ref_path, test_path, graph_output_folder):
    try:
        # Load and align
        ref_sr, ref = load_audio(ref_path, target_sr=44100, mono=True)
        test_sr, test = load_audio(test_path, target_sr=44100, mono=True)
        ref, test, _ = align_signals(ref, test)


        if ref.size == 0 or test.size == 0:
            raise ValueError("Aligned signals are empty.")

        model = PEAQ(fs=44100)
        model.process(ref, test)
        odg, movs = model.computeODG()

        base_name = os.path.splitext(os.path.basename(ref_path))[0]
        graph_path = os.path.join(graph_output_folder, f"{base_name}.png")

        # Plotting: original 4-panel plot
        frames = np.arange(len(model.BWRef))
        plt.figure(figsize=(16, 9))

        plt.subplot(4, 1, 1)
        plt.plot(frames, model.BWRef, label="Ref BW", color='blue')
        plt.title("Bandwidth of Reference Signal")
        plt.xlabel("Frame")
        plt.ylabel("BWRef")
        plt.grid(True)

        plt.subplot(4, 1, 2)
        plt.plot(frames, model.BWTest, label="Test BW", color='green')
        plt.title("Bandwidth of Test Signal")
        plt.xlabel("Frame")
        plt.ylabel("BWTest")
        plt.grid(True)

        plt.subplot(4, 1, 3)
        plt.plot(frames, np.mean(model.NMR, axis=1), label="NMR", color='orange')
        plt.title("Noise-to-Mask Ratio")
        plt.xlabel("Frame")
        plt.ylabel("NMR")
        plt.grid(True)

        plt.subplot(4, 1, 4)
        plt.plot(frames, [odg] * len(frames), label="ODG", color='red')
        plt.title("Overall Difference Grade (ODG)")
        plt.xlabel("Frame")
        plt.ylabel("ODG")
        plt.grid(True)

        plt.tight_layout()
        plt.savefig(graph_path)
        plt.close()

        # Quality classification
        quality = (
            "Excellent" if odg > -0.5 else
            "Good" if odg > -1.5 else
            "Satisfactory" if odg > -2.5 else
            "Poor"
        )

        return odg, quality

    except Exception as e:
        print(f"❌ PEAQ Analysis Failed for {ref_path}: {e}")
        return None, None


def classify_quality(odg):
    if odg >= -0.5:
        return "Excellent"
    elif odg >= -1.5:
        return "Good"
    elif odg >= -2.5:
        return "Satisfactory"
    elif odg >= -3.0:
        return "Poor"
    else:
        return "Bad"
