import numpy as np
import librosa
import sys

class PEAQ:
    def __init__(self, fs):
        """
        Initialize the PEAQ model with the given sampling frequency.
        """
        self.fs = fs
        self.X2MatR = None  # Framed reference signal
        self.X2MatT = None  # Framed test signal
        self.EbNMatR = None  # Placeholder: energy band matrix for reference
        self.EbNMatT = None  # Placeholder: energy band matrix for test
        self.EhsR = None     # Placeholder: spread excitation pattern for reference

    def process(self, ref_signal, test_signal):
        """
        Frame the input reference and test signals for block-based analysis.
        Returns the number of frames.
        """
        frame_size = 1024
        hop_size = 512
        num_frames = (len(ref_signal) - frame_size) // hop_size + 1

        # Initialize frame matrices
        self.X2MatR = np.zeros((num_frames, frame_size))
        self.X2MatT = np.zeros((num_frames, frame_size))

        for i in range(num_frames):
            start = i * hop_size
            end = start + frame_size
            self.X2MatR[i, :] = ref_signal[start:end]
            self.X2MatT[i, :] = test_signal[start:end]

        # Placeholder for perceptual energy features
        self.EbNMatR = np.abs(self.X2MatR)
        self.EbNMatT = np.abs(self.X2MatT)
        self.EhsR = np.maximum(self.EbNMatR, 1e-12)  # Avoid division by zero

        return num_frames

    def PQmovBW(self, input_pair):
        """
        Compute a basic perceptual bandwidth measure for a pair of frames.
        """
        if not isinstance(input_pair, np.ndarray) or input_pair.shape[0] != 2:
            raise ValueError("input_pair must be a 2-row numpy array (reference, test)")

        x = input_pair[0, :]
        y = input_pair[1, :]

        if x.size == 0 or y.size == 0 or x.shape != y.shape:
            return 0.0, 0.0

        # Sum of absolute differences gives an approximation of signal complexity/bandwidth
        BWRef = np.sum(np.abs(np.diff(x)))
        BWTest = np.sum(np.abs(np.diff(y)))

        return BWRef, BWTest

    def computeBW(self, X2MatR, X2MatT):
        """
        Compute bandwidth for each frame pair of reference and test signals.
        """
        num_frames = X2MatR.shape[0]
        BWRef = np.zeros(num_frames)
        BWTest = np.zeros(num_frames)

        for i in range(num_frames):
            try:
                BWRef[i], BWTest[i] = self.PQmovBW(np.vstack((X2MatR[i, :], X2MatT[i, :])))
            except Exception as e:
                print(f"Frame {i}: Bandwidth computation failed: {e}")
                BWRef[i], BWTest[i] = 0.0, 0.0

        return BWRef, BWTest

    def computeNMR(self, EbNMatT, EhsR, EbNMatR):
        """
        Compute the Noise-to-Mask Ratio (NMR), a perceptual measure of distortion.
        Returns average and maximum NMR.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            NMR = 10 * np.log10((EbNMatT + 1e-12) / (EhsR + 1e-12))
            NMRavg = np.mean(NMR)
            NMRmax = np.max(NMR)
        return NMRavg, NMRmax

    def computeODG(self, nmr_avg, nmr_max, bw_ref, bw_test, added_energy=0):
        """
        Compute the Objective Difference Grade (ODG) as a single quality score.
        ODG ranges from 0 (transparent) to -4 (very annoying distortion).
        """
        print(f"DEBUG: nmr_avg={nmr_avg:.4f}, nmr_max={nmr_max:.4f}, "
              f"bw_ref_mean={np.mean(bw_ref):.4f}, bw_test_mean={np.mean(bw_test):.4f}, "
              f"added_energy={added_energy:.6f}")

        # Simplified model for demonstration: linear combination of perceptual metrics
        odg = (0.0 
               + 0.45 * nmr_avg 
               - 0.007 * abs(np.mean(bw_ref) - np.mean(bw_test)) 
               - 0.8 * added_energy)

        print(nmr_avg)
        print(bw_ref)
        print(bw_test)
        print(added_energy)

        print(f"DEBUG: raw ODG={odg:.4f}")

        # Clamp ODG to the standard PEAQ range [-4, 0]
        odg = np.clip(odg, -4, 0)
        print(f"DEBUG: final ODG (clipped)={odg:.4f}")
        return odg

def load_audio(filename, target_fs=48000):
    """
    Load an audio file and resample it to the target sampling rate.
    """
    audio, fs = librosa.load(filename, sr=target_fs, mono=True)
    return audio

def main():
    """
    Main routine to run PEAQ-style analysis on two audio files.
    """
    if len(sys.argv) != 3:
        print("Usage: python peaq_main.py reference.wav test.wav")
        sys.exit(1)

    ref_file = sys.argv[1]
    test_file = sys.argv[2]
    fs = 48000  # Standard sampling rate

    # Load reference and test audio
    ref_signal = load_audio(ref_file, fs)
    test_signal = load_audio(test_file, fs)

    # Truncate to equal length
    minlen = min(len(ref_signal), len(test_signal))
    ref_signal = ref_signal[:minlen]
    test_signal = test_signal[:minlen]

    print(f"Loaded '{ref_file}' and '{test_file}' ({minlen} samples each)")

    # Initialize and run PEAQ processing
    peaq = PEAQ(fs)
    num_frames = peaq.process(ref_signal, test_signal)
    print(f"Processed {num_frames} frames.")

    # Compute perceptual features
    bw_ref, bw_test = peaq.computeBW(peaq.X2MatR, peaq.X2MatT)
    nmr_avg, nmr_max = peaq.computeNMR(peaq.EbNMatT, peaq.EhsR, peaq.EbNMatR)
    added_energy = np.mean(np.abs(test_signal - ref_signal))

    # Print diagnostic values
    print(f"Bandwidth Reference (mean): {np.mean(bw_ref):.2f}")
    print(f"Bandwidth Test (mean): {np.mean(bw_test):.2f}")
    print(f"NMR Avg: {nmr_avg:.2f}")
    print(f"NMR Max: {nmr_max:.2f}")
    print(f"Added energy: {added_energy:.5f}")

    # Final quality score
    odg = peaq.computeODG(nmr_avg, nmr_max, bw_ref, bw_test, added_energy)
    print(f"\nODG (Objective Difference Grade): {odg:.2f}")

if __name__ == "__main__":
    main()

