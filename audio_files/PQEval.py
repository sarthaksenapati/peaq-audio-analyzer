import numpy as np

class PQEval(object):
    def __init__(self, Amax=1, Fs=48000, NF=2048):
        self.Amax = Amax
        self.Fs = Fs
        self.NF = NF
        self.Nc = 48  # Number of critical bands
        self.framesize = NF
        self.hopsize = NF // 2  # 50% overlap

    def PQDFTFrame(self, x):
        window = np.hanning(len(x))
        X = np.fft.fft(x * window, n=self.NF)
        mag_squared = np.abs(X[:self.NF // 2]) ** 2
        norm_factor = np.sum(window ** 2)
        mag_squared /= norm_factor  # Normalize to compensate window energy loss
        return mag_squared

    def PQ_excitCB(self, X2):
        Nc = self.Nc
        EbN = np.zeros((2, Nc))
        Es = np.zeros((2, Nc))
        bins_per_band = (self.NF // 2) // Nc
        for ch in range(2):
            for k in range(Nc):
                start_bin = k * bins_per_band
                end_bin = (k + 1) * bins_per_band
                if end_bin > self.NF // 2:
                    end_bin = self.NF // 2
                EbN[ch, k] = np.sum(X2[ch, start_bin:end_bin])
                Es[ch, k] = 0.4 * EbN[ch, k]  # Increase masking threshold factor
        return EbN, Es

    def PQ_timeSpread(self, EsMat):
        Es_smooth = np.copy(EsMat)
        alpha = 0.7
        for i in range(1, EsMat.shape[0]):
            Es_smooth[i, :] = alpha * Es_smooth[i-1, :] + (1 - alpha) * EsMat[i, :]
        # Normalize smoothed energy to prevent scale blowup
        max_val = np.max(Es_smooth) + 1e-12
        Es_smooth /= max_val
        return Es_smooth

    def PQCB(self):
        Nc = self.Nc
        dz = np.full(Nc, 0.1)
        fc = np.linspace(100, 8000, Nc)
        fl = fc - dz / 2
        fu = fc + dz / 2
        return Nc, fc, fl, fu, dz