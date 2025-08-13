import subprocess
import os
import tkinter as tk
from tkinter import filedialog, messagebox

def convert_to_mp3(input_file, bitrate="192k"):
    base_name = os.path.splitext(input_file)[0]
    output_file = base_name + ".mp3"
    
    try:
        subprocess.run([
            "ffmpeg",
            "-y",                # Overwrite output
            "-i", input_file,    # Input file
            "-vn",               # Remove video if any
            "-ar", "44100",      # Audio sample rate
            "-ac", "2",          # Stereo
            "-b:a", bitrate,     # MP3 bitrate
            output_file
        ], check=True)
        messagebox.showinfo("Success", f"Conversion complete:\n{output_file}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Conversion failed:\n{e}")

def select_and_convert():
    file_path = filedialog.askopenfilename(
        title="Select a media file",
        filetypes=[("All Supported", "*.*")]
    )
    if file_path:
        convert_to_mp3(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main Tkinter window
    select_and_convert()

