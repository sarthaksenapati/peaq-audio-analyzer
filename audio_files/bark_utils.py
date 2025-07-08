import numpy as np

def fft2barkmx(nfft=2048, fs=48000, num_bands=24, width=1.0):
    """Create a Bark-scale filterbank matrix to map FFT bins to Bark bands."""
    f = np.linspace(0, fs/2, nfft//2 + 1)
    bark_f = 6 * np.arcsinh(f / 600)  # Bark scale approximation
    band_edges = np.linspace(bark_f[0], bark_f[-1], num_bands + 2)

    W = np.zeros((num_bands, len(f)))
    for i in range(num_bands):
        low, center, high = band_edges[i], band_edges[i+1], band_edges[i+2]
        for j, bval in enumerate(bark_f):
            if bval < low:
                W[i, j] = 0
            elif bval < center:
                W[i, j] = (bval - low) / (center - low)
            elif bval < high:
                W[i, j] = (high - bval) / (high - center)
            else:
                W[i, j] = 0
    return W
