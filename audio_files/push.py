import os
import subprocess
import time
import tkinter as tk
from tkinter import filedialog

# === SETTINGS ===
DEVICE_FOLDER = "/sdcard/O6/"
FILES_APP_PACKAGE = "com.google.android.apps.nbu.files"

def adb(cmd):
    result = subprocess.run(["adb"] + cmd.split(), capture_output=True, text=True)
    return result.stdout.strip() + result.stderr.strip()

def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Audio File to Push",
        filetypes=[("Audio Files", "*.wav *.mp3 *.flac *.aac *.m4a *.ogg"), ("All Files", "*.*")]
    )
    return file_path

def push_and_index(file_path):
    file_name = os.path.basename(file_path)
    print(f"📤 Pushing {file_name} to {DEVICE_FOLDER}...")
    print(adb(f'push "{file_path}" "{DEVICE_FOLDER}"'))

    print("📅 Touching file to update modified time...")
    print(adb(f'shell touch "{DEVICE_FOLDER}{file_name}"'))

    print("📡 Triggering media scanner...")
    print(adb(f'shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{DEVICE_FOLDER}{file_name}'))

    print("🔁 Restarting Files by Google app...")
    adb(f"shell am force-stop {FILES_APP_PACKAGE}")
    time.sleep(0.5)
    adb(f"shell monkey -p {FILES_APP_PACKAGE} 1")

    print("⏳ Waiting briefly to allow indexing...")
    time.sleep(3)

    print(f"✅ Done. Now check Files by Google → Audio → O6 tab for '{file_name}'.")

if __name__ == "__main__":
    selected = select_file()
    if not selected:
        print("❌ No file selected.")
    else:
        push_and_index(selected)
