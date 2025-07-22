# file_manager.py

import os
from tkinter import Tk, filedialog

# ✅ List of common audio formats supported by FFmpeg
SUPPORTED_AUDIO_EXTENSIONS = "*.wav *.mp3 *.m4a *.flac *.aac *.ogg *.opus"

def select_audio_files():
    root = Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(
        title="Select Audio Files",
        filetypes=[
            ("Supported audio files", SUPPORTED_AUDIO_EXTENSIONS.split()),
            ("All files", "*.*")
        ]
    )
    root.destroy()
    return files

def ensure_dir_exists(path):
    os.makedirs(path, exist_ok=True)
