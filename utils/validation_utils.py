# utils/validation_utils.py

import os

def validate_wav_file(path):
    return path.lower().endswith(".wav") and os.path.isfile(path)
