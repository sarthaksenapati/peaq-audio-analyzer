# spotify_mode.py
import os
import shutil
import subprocess
from datetime import datetime
import pandas as pd

from trim_utils import split_audio_by_durations
from spotify import (
    list_audio_input_devices,
    adb,
    launch_gaana,
    launch_jiosaavn,
    launch_audible
)

from config import (
    excel_path,
    recording_phone,
    selected_audio_device,
    playback_app
)


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


def main():
    print("🎵 Spotify RECORD MODE: Batch Playlist Capture")

    # Step 1: Validate Excel file
    if not os.path.isfile(excel_path):
        print(f"❌ Excel file not found at: {excel_path}")
        return
    print(f"📄 Using Excel from config: {excel_path}")

    # Step 2: Calculate total recording duration
    total_duration = calculate_total_duration_from_excel(excel_path)
    print(f"⏱ Total Duration to Record: {total_duration} seconds")

    # Step 3: Validate audio input device
    devices = list_audio_input_devices()
    if selected_audio_device not in devices:
        print(f"❌ Audio device '{selected_audio_device}' not found. Available:")
        for d in devices:
            print(f" - {d}")
        return
    print(f"🎤 Using audio device: {selected_audio_device}")

    # Step 4: Prepare recording
    phone = recording_phone.strip().lower()
    output_filename = f"{phone}_spotify_raw.wav"
    print(f"💾 Recording will be saved to: {output_filename}")

    # Step 5: Launch the correct app
    app_choice = playback_app.strip().lower()
    print(f"📱 Using playback app from config: {app_choice}")
    print("⏳ Load playlist and pause it manually. Press Enter when ready.")
    input("▶️ Press Enter to begin recording...")

    if app_choice == 'audible':
        launch_audible()
        app_package = "com.audible.application"
        adb("shell input keyevent 126")
    elif app_choice == 'gaana':
        launch_gaana()
        app_package = "com.gaana"
        adb("shell input keyevent 85")
    elif app_choice == 'jiosaavn':
        launch_jiosaavn()
        app_package = "com.jio.media.jiobeats"
        adb("shell input keyevent 85")
    elif app_choice == 'spotify':
        from spotify_playback import launch_and_play_spotify_playlist
        launch_and_play_spotify_playlist()
        app_package = "com.spotify.music"
    else:
        print("⚠️ Invalid app in config. Defaulting to Audible.")
        launch_audible()
        app_package = "com.audible.application"
        adb("shell input keyevent 85")

    # Step 6: Record
    print("🎙 Recording started...")
    record_audio(selected_audio_device, total_duration, output_filename)

    # Step 7: Stop playback app
    if app_package == "com.spotify.music":
        adb("shell input keyevent 127")
    else:
        adb("shell input keyevent 85")
    subprocess.run(["adb", "shell", "am", "force-stop", app_package])
    print(f"🛑 {app_package} stopped. Recording complete.")

    # Step 8: Split long recording into individual tracks
    print("✂️ Splitting long recording into individual tracks...")
    split_output_folder = f"{phone}_tracks"
    if os.path.exists(split_output_folder):
        shutil.rmtree(split_output_folder)
    os.makedirs(split_output_folder, exist_ok=True)

    split_audio_by_durations(
        input_audio=output_filename,
        excel_path=excel_path,
        output_dir=split_output_folder
    )

    print(f"✅ All tracks saved in: {split_output_folder}")


if __name__ == "__main__":
    main()