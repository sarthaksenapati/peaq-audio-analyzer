# playback_options.py
import os
import time
import subprocess
import urllib.parse
import wave
import contextlib
from tkinter import filedialog

FILES_APP_PACKAGE = "com.google.android.apps.nbu.files"
FILES_TAP_X, FILES_TAP_Y = 221, 700  # Update if needed
FILES_TARGET_FOLDER = "/sdcard/O6/"
EXTRACTED_DIR = "extracted_audio"

os.makedirs(EXTRACTED_DIR, exist_ok=True)

def adb(cmd):
    result = subprocess.run(["adb"] + cmd.split(), capture_output=True, text=True)
    return result.stdout.strip() + result.stderr.strip()

def get_wav_duration(filepath):
    with contextlib.closing(wave.open(filepath, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        return frames / float(rate)

def trim_audio_with_ffmpeg(input_path, output_path, start_time, duration):
    import subprocess
    try:
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-c:a", "pcm_s16le",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"FFmpeg error: {e}")
        return False

def play_via_default_player(file_path):
    """Launch default media player (e.g., YT Music)"""
    filename = os.path.basename(file_path)
    device_path = f"/sdcard/{filename}"
    os.system(f"adb push \"{file_path}\" \"{device_path}\"")
    escaped_path = urllib.parse.quote(device_path)
    mime_type = get_mime_type(file_path)
    subprocess.run([
        "adb", "shell", "am", "start", "-a", "android.intent.action.VIEW",
        "-d", f"file://{escaped_path}", "-t", mime_type
    ], capture_output=True)

def play_via_files_app(file_path):
    """Launch , tap to play, kill after playback, then trim audio"""
    import glob

    def latest_recording_file():
        files = glob.glob("recordings/*.mp4")
        if not files:
            return None
        return max(files, key=os.path.getmtime)

    filename = os.path.basename(file_path)
    remote_path = f"{FILES_TARGET_FOLDER}{filename}"

    # ✅ Push file
    subprocess.run(["adb", "push", file_path, FILES_TARGET_FOLDER], capture_output=True)
    adb(f'shell touch "{remote_path}"')
    adb(f'shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{remote_path}')

    duration = get_wav_duration(file_path)
    print(f"🎵 Duration: {duration:.2f}s")

    # ✅ Start playback
    print("🚀 Launching Files app...")
    adb(f"shell monkey -p {FILES_APP_PACKAGE} 1")
    recording_start = time.time()
    time.sleep(2.0)

    print(f"👆 Sending tap at ({FILES_TAP_X},{FILES_TAP_Y})")
    adb(f"shell input tap {FILES_TAP_X} {FILES_TAP_Y}")
    tap_time = time.time()

    # ✅ Wait then kill
    end_buffer = 1
    wait_time = duration + end_buffer
    print(f"⏳ Waiting {wait_time:.2f} seconds before killing Files app...")
    time.sleep(wait_time)

    print("❌ Force-stopping Files app...")
    adb(f"shell am force-stop {FILES_APP_PACKAGE}")
    recording_stop = time.time()

    # ✅ Trim recording
    try:
        recording_path = latest_recording_file()
        if not recording_path:
            print("❌ No screen recording found to trim.")
            return

        print(f"🎞️ Detected screen recording: {recording_path}")

        tap_delay = tap_time - recording_start
        trim_duration = duration + end_buffer

        base = os.path.splitext(filename)[0]
        out_path = os.path.join(EXTRACTED_DIR, f"{base}_clean.wav")

        print(f"✂️ Trimming from {tap_delay:.2f}s for {trim_duration:.2f}s...")
        success = trim_audio_with_ffmpeg(recording_path, out_path, tap_delay, trim_duration)

        if success:
            print(f"✅ Clean audio saved: {out_path}")
        else:
            print("❌ FFmpeg trimming failed.")
    except Exception as e:
        print(f"❌ Trimming error: {e}")


def get_mime_type(file_path):
    ext = file_path.lower().split(".")[-1]
    return {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "flac": "audio/flac"
    }.get(ext, "audio/*")

def choose_playback_method():
    print("\n🎧 Choose Playback Method:")
    print("  [1] Default Media Player (YT Music or system default)")
    print("  [2] File Manager Playback")
    choice = input("> ").strip()
    if choice == '2':
        return play_via_files_app
    return play_via_default_player
