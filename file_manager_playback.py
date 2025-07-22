import os
import time
import subprocess

FILES_APP_PACKAGE = "com.google.android.apps.nbu.files"
FILES_TAP_X, FILES_TAP_Y = 221, 700
FILES_TARGET_FOLDER = "/sdcard/O6/"

def adb(cmd):
    result = subprocess.run(["adb"] + cmd.split(), capture_output=True, text=True)
    return result.stdout.strip() + result.stderr.strip()

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

def play_via_files_app(file_path, on_kill_callback=None):
    filename = os.path.basename(file_path)
    remote_path = f"{FILES_TARGET_FOLDER}{filename}"

    subprocess.run(["adb", "push", file_path, FILES_TARGET_FOLDER], capture_output=True)
    adb(f'shell touch "{remote_path}"')
    adb(f'shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{remote_path}')

    duration = get_audio_duration(file_path)
    print(f"🎵 Duration: {duration:.2f}s")

    print("🚀 Launching Files app...")
    adb(f"shell monkey -p {FILES_APP_PACKAGE} 1")
    time.sleep(2)

    print(f"👆 Sending tap at ({FILES_TAP_X},{FILES_TAP_Y})")
    adb(f"shell input tap {FILES_TAP_X} {FILES_TAP_Y}")
    tap_time = time.time()

    wait_time = duration + 1
    print(f"⏳ Waiting {wait_time:.2f} seconds before killing Files app...")
    time.sleep(wait_time)

    print("❌ Force-stopping Files app...")
    adb(f"shell am force-stop {FILES_APP_PACKAGE}")

    if on_kill_callback:
        print("⏹️ Stopping AUX recording after playback finishes...")
        on_kill_callback()