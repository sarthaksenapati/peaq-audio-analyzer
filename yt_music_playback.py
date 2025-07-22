import os
import time
import subprocess
import urllib.parse

def get_audio_duration(filepath):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filepath],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"❌ Could not get duration for {filepath}: {e}")
        return 0.0

def get_mime_type(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    return {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
    }.get(ext, "audio/*")

def play_via_yt_music(file_path, on_kill_callback=None):
    filename = os.path.basename(file_path)
    device_path = f"/sdcard/{filename}"
    os.system(f'adb push "{file_path}" "{device_path}"')
    escaped_path = urllib.parse.quote(device_path)
    mime_type = get_mime_type(file_path)

    duration = get_audio_duration(file_path)
    print(f"🎵 Duration: {duration:.2f}s")

    print("⏳ Waiting 3s after starting recording before launching YT Music...")
    time.sleep(3)  # ❗ Delay here BEFORE triggering autoplay

    print("🚀 Launching YT Music with intent (this auto-plays)...")
    subprocess.run([
        "adb", "shell", "am", "start", "-a", "android.intent.action.VIEW",
        "-d", f"file://{escaped_path}", "-t", mime_type
    ], capture_output=True)

    wait_time = duration + 1
    print(f"⏳ Waiting {wait_time:.2f}s for audio to finish...")
    time.sleep(wait_time)

    if on_kill_callback:
        print("⏹️ Stopping AUX recording after playback finishes...")
        on_kill_callback()
