import subprocess
import time
from datetime import datetime

SPOTIFY_PACKAGE = "com.spotify.music"

def adb(cmd):
    return subprocess.run(["adb"] + cmd.split(), capture_output=True, text=True).stdout.strip()

AUDIBLE_PACKAGE = "com.audible.application"

def launch_audible():
    print("[Audible] Launching app...")
    subprocess.run([
        "adb", "shell", "monkey",
        "-p", AUDIBLE_PACKAGE,
        "-c", "android.intent.category.LAUNCHER", "1"
    ])
    time.sleep(2.0)

JIOSAAVN_PACKAGE = "com.jio.media.jiobeats"

def launch_jiosaavn():
    print("[JioSaavn] Launching app...")
    subprocess.run([
        "adb", "shell", "monkey",
        "-p", JIOSAAVN_PACKAGE,
        "-c", "android.intent.category.LAUNCHER", "1"
    ])
    time.sleep(2.0)

GAANA_PACKAGE = "com.gaana"

def launch_gaana():
    print("[Gaana] Launching app...")
    subprocess.run([
        "adb", "shell", "monkey",
        "-p", GAANA_PACKAGE,
        "-c", "android.intent.category.LAUNCHER", "1"
    ])
    time.sleep(2.0)

def launch_spotify():
    print("[Spotify] Launching app...")
    subprocess.run([
        "adb", "shell", "monkey",
        "-p", SPOTIFY_PACKAGE,
        "-c", "android.intent.category.LAUNCHER", "1"
    ])
    time.sleep(2.0)

def list_audio_input_devices():
    print("🔍 Scanning for available audio input devices...\n")
    result = subprocess.run(
        ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True
    )
    lines = result.stderr.splitlines()
    devices = []
    for line in lines:
        if "Alternative name" in line:
            continue
        if "dshow" in line and "Audio input" in line:
            continue
        if "dshow" in line and '"' in line:
            device_name = line.split('"')[1]
            devices.append(device_name)
    return devices

def get_user_duration():
    while True:
        raw = input("Enter track duration (mm:ss): ").strip()
        try:
            minutes, seconds = map(int, raw.split(":"))
            return minutes * 60 + seconds
        except:
            print("Invalid format. Use mm:ss (e.g., 4:08)")

def main():
    # Step 1: Select audio input device
    devices = list_audio_input_devices()
    print("\n🎤 Available Audio Devices:")
    for idx, name in enumerate(devices):
        print(f"[{idx}] {name}")
    selected = int(input("\nSelect device index to use: "))
    device_name = devices[selected]

    # Step 2: Get duration (+1 second buffer)
    duration_sec = get_user_duration()
    duration_with_buffer = duration_sec + 1

    # Step 3: Launch Spotify
    input("[Ready] Open Spotify to the correct track and pause it. Press Enter to launch and start recording...")
    launch_spotify()

    # Step 4: Start playback
    print("[Spotify] Sending PLAY toggle (keyevent 85)...")
    adb("shell input keyevent 85")

    # Step 5: Start recording with FFmpeg
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"spotify_recording_{timestamp}.wav"
    print(f"[Recording] Recording for {duration_with_buffer} seconds to: {output_path}")

    ffmpeg_cmd = [
        "ffmpeg",
        "-f", "dshow",
        "-i", f"audio={device_name}",
        "-t", str(duration_with_buffer),
        output_path
    ]
    subprocess.run(ffmpeg_cmd)
    
    # Step 6: Stop Spotify and exit
    print("[Spotify] Sending PAUSE (keyevent 127) and killing app...")
    adb("shell input keyevent 127")
    subprocess.run(["adb", "shell", "am", "force-stop", SPOTIFY_PACKAGE])

    print(f"[Done] Recording complete: {output_path}")

if __name__ == "__main__":
    main()
