#PQEval
import numpy as np
from scipy.signal import fftconvolve

class PQEval: 
    def __init__(self, Amax=1, Fs=48000, NF=2048):
        self.Amax = Amax
        self.Fs = Fs
        self.NF = NF
        self.Nc = 24  # Number of Bark bands (simplified)
        self.framesize = NF
        self.hopsize = NF // 2  # 50% overlap
        self.freqs = np.fft.rfftfreq(NF, 1.0 / Fs)  # FFT bin frequencies
        
        # Bark band edges (Hz) - simplified model
        self.bark_bands = np.array([
            0, 100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480,
            1720, 2000, 2320, 2700, 3150, 3700, 4400, 5300, 6400, 7700, 9500, 12000
        ])
        
        # Spreading function (dB -> linear scale)
        self.spread = self._generate_spreading_function()

    def _generate_spreading_function(self):
        """Create a spreading function to simulate masking across Bark bands."""
        bark_diff = np.arange(-12, 13)  # ±12 Bark bands
        spread_db = 15.81 + 7.5 * (bark_diff + 0.474) - 17.5 * np.sqrt(1 + (bark_diff + 0.474)**2)
        return 10 ** (spread_db / 10)  # Convert dB to linear scale

    def PQDFTFrame(self, x):
        """Compute normalized FFT power spectrum with Hanning window."""
        window = np.hanning(len(x))
        X = np.fft.rfft(x * window, n=self.NF)
        X2 = np.abs(X) ** 2
        X2 /= np.sum(window ** 2)  # Compensate for window energy
        return X2

    def PQ_excitCB(self, X2):
        """Map FFT bins to Bark bands and apply spreading."""
        # Sum energy within each Bark band
        bark_energy = np.zeros(self.Nc)
        for i in range(self.Nc - 1):
            mask = (self.freqs >= self.bark_bands[i]) & (self.freqs < self.bark_bands[i+1])
            bark_energy[i] = np.sum(X2[mask])
        
        # Apply spreading function (convolution)
        spread_energy = fftconvolve(bark_energy, self.spread, mode='same')
        return bark_energy, spread_energy

    def PQ_timeSpread(self, EsMat):
        """Temporal masking: smooth energy across frames."""
        alpha = 0.7  # Smoothing factor
        Es_smooth = np.zeros_like(EsMat)
        Es_smooth[0] = EsMat[0]
        for i in range(1, EsMat.shape[0]):
            Es_smooth[i] = alpha * Es_smooth[i-1] + (1 - alpha) * EsMat[i]
        return Es_smooth

    def PQCB(self):
        """Return critical band parameters (for debugging)."""
        return self.bark_bands