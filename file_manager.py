import os
from tkinter import Tk, filedialog

# ✅ Expanded list of audio formats, including mid, mp4, wma
SUPPORTED_AUDIO_EXTENSIONS = "*.wav *.mp3 *.m4a *.flac *.aac *.ogg *.opus *.wma *.webm *.mid *.mp4"

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
