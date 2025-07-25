import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import subprocess
from datetime import datetime
from trim_utils import split_audio_by_durations  # make sure this exists
from spotify import list_audio_input_devices, launch_spotify, adb, launch_gaana, launch_jiosaavn, launch_audible


# 📁 Ask user to select Excel file using GUI
def select_excel_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Excel File",
        filetypes=[("Excel Files", "*.xlsx *.xls")]
    )
    return file_path


# 🧠 Robustly parse duration formats
def parse_duration(duration_str):
    if isinstance(duration_str, str) and ':' in duration_str:
        try:
            minutes, seconds = map(int, duration_str.strip().split(":"))
            return minutes * 60 + seconds
        except Exception:
            return None
    try:
        return int(float(duration_str))
    except Exception:
        return None


# ⏱ Sum total track durations from Excel
def calculate_total_duration_from_excel(excel_path):
    df = pd.read_excel(excel_path)
    if "duration" not in df.columns:
        raise ValueError("Excel must have a 'duration' column (in seconds or MM:SS).")

    durations = df["duration"].dropna()
    total_seconds = 0

    for val in durations:
        seconds = parse_duration(val)
        if seconds is None:
            print(f"❌ Skipping invalid duration format: {val}")
            continue
        total_seconds += seconds

    return total_seconds


def record_audio(device_name, total_duration_sec, output_path):
    duration_with_buffer = total_duration_sec + 1
    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "dshow",
        "-i", f"audio={device_name}",
        "-t", str(duration_with_buffer),
        output_path
    ]
    subprocess.run(ffmpeg_cmd)


def main():
    print("🎵 Spotify RECORD MODE: Batch Playlist Capture")

    # Step 1: Select Excel file with durations
    excel_path = select_excel_file()
    if not excel_path:
        print("❌ No file selected. Exiting.")
        return
    print(f"📄 Selected Excel: {excel_path}")

    # Step 2: Sum durations
    total_duration = calculate_total_duration_from_excel(excel_path)
    print(f"⏱ Total Duration to Record: {total_duration} seconds")

    # Step 3: Select audio input device
    devices = list_audio_input_devices()
    print("\n🎤 Available Audio Devices:")
    for idx, name in enumerate(devices):
        print(f"[{idx}] {name}")
    selected = int(input("Select device index to use: "))
    device_name = devices[selected]

    # Step 4: Prepare recording
    phone = input("Which phone is this recording for? (phone1/phone2): ").strip().lower()
    output_filename = f"{phone}_spotify_raw.wav"
    print(f"💾 Recording will be saved to: {output_filename}")

    # Step 5: Launch Spotify and begin playback
    input("📱 Load Spotify to the start of the playlist and pause. Press Enter to start...")
    launch_audible()
    adb("shell input keyevent 85")  # Play

    # Step 6: Record
    print("🎙 Recording started...")
    record_audio(device_name, total_duration, output_filename)

    # Step 7: Kill Spotify
    adb("shell input keyevent 127")  # Pause
    subprocess.run(["adb", "shell", "am", "force-stop", "com.audible.application"])
    print("🛑 Spotify stopped. Recording complete.")

    # Step 8: Split
    print("✂️ Splitting long recording into individual tracks...")
    split_output_folder = f"{phone}_tracks"
    os.makedirs(split_output_folder, exist_ok=True)
    split_audio_by_durations(
        input_audio=output_filename,
        excel_path=excel_path,
        output_dir=split_output_folder
    )

    print(f"✅ All tracks saved in: {split_output_folder}")


if __name__ == "__main__":
    main()
