#PEAQ
import numpy as np
from .PQEval import PQEval

class PEAQ:
    def __init__(self, fs):
        self.fs = fs
        self.pq_eval = PQEval(Fs=fs)
        self.EbNMatR = None
        self.EbNMatT = None
        self.EhsR = None
        self.BWRef = None
        self.BWTest = None
        self.NMR = None
        self.added_energy = None

    def process(self, ref_signal, test_signal):
        frame_size = self.pq_eval.framesize
        hop_size = self.pq_eval.hopsize
        num_frames = (len(ref_signal) - frame_size) // hop_size + 1

        self.EbNMatR = np.zeros((num_frames, self.pq_eval.Nc))
        self.EbNMatT = np.zeros((num_frames, self.pq_eval.Nc))
        self.EhsR = np.zeros((num_frames, self.pq_eval.Nc))

        for i in range(num_frames):
            start = i * hop_size
            frame_R = ref_signal[start:start+frame_size]
            frame_T = test_signal[start:start+frame_size]

            X2_R = self.pq_eval.PQDFTFrame(frame_R)
            X2_T = self.pq_eval.PQDFTFrame(frame_T)
            self.EbNMatR[i], self.EhsR[i] = self.pq_eval.PQ_excitCB(X2_R)
            self.EbNMatT[i], _ = self.pq_eval.PQ_excitCB(X2_T)

        # Compute per-frame bandwidth
        weights = np.arange(self.pq_eval.Nc)
        self.BWRef = np.sum(self.EbNMatR * weights, axis=1)
        self.BWTest = np.sum(self.EbNMatT * weights, axis=1)
        
        # Compute added energy
        self.added_energy = np.mean(np.abs(test_signal - ref_signal))
        
        return num_frames

    def computeNMR(self):
        eps = 1e-12
        band_weights = 1.0 / (1 + np.arange(self.pq_eval.Nc)/5)
        self.NMR = 10 * np.log10((self.EbNMatT + eps) / (self.EhsR + eps))
        return np.mean(self.NMR * band_weights)

    def computeADB(self, threshold_db=-30):
        if self.NMR is None:
            self.computeNMR()
        distorted_frames = np.any(self.NMR > threshold_db, axis=1)
        return np.log10(np.sum(distorted_frames) / len(distorted_frames) + 1e-12)

    def computeMFPD(self):
        if self.NMR is None:
            self.computeNMR()
        prob = 1 / (1 + np.exp(-0.6 * (self.NMR - 5)))
        return np.max(prob)

    def computeODG(self):
        NMR_avg = self.computeNMR()
        ADB = self.computeADB()
        MFPD = self.computeMFPD()
        AvgBwRef = np.mean(self.BWRef)
        AvgBwTst = np.mean(self.BWTest)
        
        odg = (
            -0.25 * NMR_avg
            - 0.1 * abs(AvgBwRef - AvgBwTst)
            - 0.3 * ADB
            - 0.35 * MFPD
            - 0.5 * self.added_energy
        )
        
        movs = {
            'AvgBwRef': float(AvgBwRef),
            'AvgBwTst': float(AvgBwTst),
            'NMRtotB': float(NMR_avg),
            'ADB': float(ADB),
            'MFPD': float(MFPD)
        }
        
        return np.clip(odg, -4, 0), movs