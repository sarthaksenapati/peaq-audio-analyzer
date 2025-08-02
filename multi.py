import threading
import time
import os
import subprocess
import shutil
import pandas as pd
from datetime import datetime

from trim_utils import split_audio_by_durations
from spotify import (
    list_audio_input_devices,
    launch_gaana,
    launch_jiosaavn,
    launch_audible,
)
from config import excel_path
from spotify_playback import launch_and_play_spotify_playlist

def get_adb_devices():
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    devices = []
    for line in lines[1:]:
        if line.strip() and "device" in line:
            serial = line.split()[0]
            devices.append(serial)
    return devices

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
        "-y",
        "-f", "dshow",
        "-i", f"audio={device_name}",
        "-t", str(duration_with_buffer),
        output_path
    ]
    subprocess.run(ffmpeg_cmd)

def run_for_device(phone_label, audio_device, app_choice, excel_path, adb_serial):
    print(f"\n=== Starting for {phone_label} ({adb_serial}) ===")
    total_duration = calculate_total_duration_from_excel(excel_path)
    output_filename = f"{phone_label}_spotify_raw.wav"
    print(f"Recording will be saved to: {output_filename}")

    print(f"Load playlist and pause it manually on {phone_label}. Press Enter when ready.")
    input(f"[{phone_label}] ▶️ Press Enter to begin recording...")

    def adb_with_serial(cmd):
        return subprocess.run(["adb", "-s", adb_serial] + cmd.split(), capture_output=True, text=True).stdout.strip()

    if app_choice == 'audible':
        subprocess.run(["adb", "-s", adb_serial, "shell", "monkey", "-p", "com.audible.application", "-c", "android.intent.category.LAUNCHER", "1"])
        app_package = "com.audible.application"
        adb_with_serial("shell input keyevent 126")
    elif app_choice == 'gaana':
        subprocess.run(["adb", "-s", adb_serial, "shell", "monkey", "-p", "com.gaana", "-c", "android.intent.category.LAUNCHER", "1"])
        app_package = "com.gaana"
        adb_with_serial("shell input keyevent 85")
    elif app_choice == 'jiosaavn':
        subprocess.run(["adb", "-s", adb_serial, "shell", "monkey", "-p", "com.jio.media.jiobeats", "-c", "android.intent.category.LAUNCHER", "1"])
        app_package = "com.jio.media.jiobeats"
        adb_with_serial("shell input keyevent 85")
    elif app_choice == 'spotify':
        launch_and_play_spotify_playlist(adb_serial=adb_serial)
        app_package = "com.spotify.music"
    else:
        print("⚠️ Invalid app. Defaulting to Audible.")
        subprocess.run(["adb", "-s", adb_serial, "shell", "monkey", "-p", "com.audible.application", "-c", "android.intent.category.LAUNCHER", "1"])
        app_package = "com.audible.application"
        adb_with_serial("shell input keyevent 126")

    print(f"[{phone_label}] 🎙 Recording started...")
    record_audio(audio_device, total_duration, output_filename)

    # Stop playback app
    if app_package == "com.spotify.music":
        adb_with_serial("shell input keyevent 127")
    else:
        adb_with_serial("shell input keyevent 85")
    subprocess.run(["adb", "-s", adb_serial, "shell", "am", "force-stop", app_package])
    print(f"[{phone_label}] 🛑 {app_package} stopped. Recording complete.")

    # Split tracks
    print(f"[{phone_label}] ✂️ Splitting long recording into individual tracks...")
    split_output_folder = f"{phone_label}_tracks"
    if os.path.exists(split_output_folder):
        shutil.rmtree(split_output_folder)
    os.makedirs(split_output_folder, exist_ok=True)
    split_audio_by_durations(
        input_audio=output_filename,
        excel_path=excel_path,
        output_dir=split_output_folder
    )
    print(f"[{phone_label}] ✅ All tracks saved in: {split_output_folder}")

def main():
    print(f"Using Excel file from config: {excel_path}")

    devices = get_adb_devices()
    if len(devices) < 1:
        print("❌ No ADB devices found.")
        return

    print("\nConnected ADB devices:")
    for idx, serial in enumerate(devices):
        print(f"[{idx}] {serial}")

    num_devices = int(input("How many devices? (1 or 2): ").strip())
    phone_serials = {}

    if num_devices == 1:
        idx = int(input("Select device index for phone1: "))
        phone_serials["phone1"] = devices[idx]
    elif num_devices == 2:
        idx1 = int(input("Select device index for phone1: "))
        idx2 = 1 - idx1 if len(devices) == 2 else int(input("Select device index for phone2: "))
        phone_serials["phone1"] = devices[idx1]
        phone_serials["phone2"] = devices[idx2]
    else:
        print("❌ Invalid number of devices.")
        return

    audio_devices = list_audio_input_devices()
    print("\n🎤 Available Audio Devices:")
    for idx, name in enumerate(audio_devices):
        print(f"[{idx}] {name}")

    threads = []
    for phone_label in sorted(phone_serials.keys()):
        adb_serial = phone_serials[phone_label]
        audio_idx = int(input(f"Select audio device index for {phone_label}: "))
        audio_device = audio_devices[audio_idx]
        app_choice = input(f"Which app for {phone_label}? (audible/gaana/jiosaavn/spotify): ").strip().lower()
        t = threading.Thread(
            target=run_for_device,
            args=(phone_label, audio_device, app_choice, excel_path, adb_serial)
        )
        threads.append(t)

    for t in threads:
        t.start()
        time.sleep(1)  # slight stagger to avoid ADB collision

    for t in threads:
        t.join()

    print("\nAll device recordings and splits complete.")

if __name__ == "__main__":
    main()