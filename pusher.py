import os
import subprocess
import time
import tkinter as tk
from tkinter import filedialog
import wave
import contextlib

FILES_APP_PACKAGE = "com.google.android.apps.nbu.files"
TARGET_FOLDER = "/sdcard/O6/"
TAP_X, TAP_Y = 221, 700  # Tap coordinates for playback

def adb(cmd):
    result = subprocess.run(["adb"] + cmd.split(), capture_output=True, text=True)
    return result.stdout.strip() + result.stderr.strip()

def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Audio File to Push",
        filetypes=[("Audio Files", "*.wav"), ("All Files", "*.*")]
    )
    return file_path

def get_wav_duration(filepath):
    with contextlib.closing(wave.open(filepath, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        return frames / float(rate)

def is_file_stable(path, wait_time=2.0):
    size1 = os.path.getsize(path)
    time.sleep(wait_time)
    size2 = os.path.getsize(path)
    return size1 == size2

def push_play_and_kill(file_path):
    file_name = os.path.basename(file_path)

    # ✅ Check file stability before pushing
    if not is_file_stable(file_path):
        print("❌ File size still changing. Aborting.")
        return

    # ✅ Get duration
    duration = get_wav_duration(file_path)
    print(f"🎵 Detected Duration: {duration:.2f} seconds")

    # ✅ Push to /sdcard/O6/
    print(f"📤 Pushing '{file_name}' to {TARGET_FOLDER}...")
    os.system(f'adb push "{file_path}" "{TARGET_FOLDER}"')
    adb(f'shell touch "{TARGET_FOLDER}{file_name}"')
    adb(f'shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{TARGET_FOLDER}{file_name}')

    # ✅ Launch Files app
    print("🚀 Launching Files app...")
    adb(f"shell monkey -p {FILES_APP_PACKAGE} 1")
    time.sleep(2)

    # ✅ Tap to start playback
    print(f"👆 Sending tap at ({TAP_X},{TAP_Y}) to play...")
    adb(f"shell input tap {TAP_X} {TAP_Y}")

    # ⏳ WAIT UNTIL THE SONG ENDS
    # --------------------------------------------
    # 🟨 THIS IS WHERE YOU TUNE THE TIMING
    # Increase or decrease this buffer to ensure
    # the full song plays but the next one doesn't
    #
    # Recommended starting value: 0.4 seconds buffer
    # --------------------------------------------
    buffer_after_song = 0.7  # << Change this value as needed
    wait_time = duration + buffer_after_song
    print(f"⏳ Waiting {wait_time:.2f} seconds to allow full playback...")
    time.sleep(wait_time)

    # ✅ Kill Files app to prevent next song
    print("❌ Force-stopping Files by Google...")
    adb(f"shell am force-stop {FILES_APP_PACKAGE}")

    print("✅ Done.")

if __name__ == "__main__":
    file_path = select_file()
    if file_path:
        push_play_and_kill(file_path)
    else:
        print("❌ No file selected.")

