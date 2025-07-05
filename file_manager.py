# file_manager.py

import os
from tkinter import Tk, filedialog

def select_audio_files():
    root = Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(filetypes=[("WAV", "*.wav")])
    root.destroy()
    return files

def ensure_dir_exists(path):
    os.makedirs(path, exist_ok=True)
