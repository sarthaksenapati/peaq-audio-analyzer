# utils/plotting_utils.py

import matplotlib.pyplot as plt
import numpy as np

import numpy as np
import matplotlib.pyplot as plt

def plot_peaq_results(peaq, output_path=None, show=True):
    frames = np.arange(len(peaq.EbNMatR))

    plt.figure(figsize=(16, 12))

    # 1. Bandwidth per frame
    plt.subplot(4, 1, 1)
    plt.plot(frames, peaq.BWRef, label="Reference")
    plt.plot(frames, peaq.BWTest, label="Test")
    plt.ylabel("Bandwidth")
    plt.legend()
    plt.title("Bandwidth per Frame")
    plt.grid(True, alpha=0.3)

    # 2. NMR per frame
    plt.subplot(4, 1, 2)
    plt.plot(frames, peaq.NMR.mean(axis=1), color='orange')
    plt.ylabel("NMR (dB)")
    plt.title("Noise-to-Mask Ratio per Frame")
    plt.grid(True, alpha=0.3)

    # 3. ODG components
    plt.subplot(4, 1, 3)
    plt.plot(frames, -0.25 * peaq.NMR.mean(axis=1), label="NMR Contribution", color='red')
    plt.plot(frames, -0.1 * np.abs(peaq.BWRef - peaq.BWTest), label="BW Difference", color='blue')
    plt.ylabel("ODG Components")
    plt.legend()
    plt.title("ODG Component Contributions")
    plt.grid(True, alpha=0.3)

    # 4. Probability of detection
    plt.subplot(4, 1, 4)
    prob = 1 / (1 + np.exp(-0.6 * (peaq.NMR - 5)))
    plt.plot(frames, np.max(prob, axis=1), color='purple')
    plt.ylabel("Detection Probability")
    plt.xlabel("Frame")
    plt.title("Maximum Probability of Detection per Frame")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path)
    if show:
        plt.show()
    else:
        plt.close()

