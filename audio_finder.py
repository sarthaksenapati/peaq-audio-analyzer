import subprocess
import re

def list_dshow_audio_devices(ffmpeg_path="ffmpeg"):
    print("🔍 Scanning for available audio input devices...\n")
    print(f"[DEBUG] Using ffmpeg at: {ffmpeg_path}")
    
    result = subprocess.run(
        [ffmpeg_path, "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )

    devices_output = result.stderr
    device_lines = [line.strip() for line in devices_output.splitlines() if "audio devices" in line or '"' in line]

    audio_devices = []
    for line in device_lines:
        match = re.search(r'"([^"]+)"', line)
        if match:
            audio_devices.append(match.group(1))
    
    if not audio_devices:
        print("❌ No audio input devices found.")
    else:
        print("🎤 Available Audio Devices:")
        for i, dev in enumerate(audio_devices):
            print(f"[{i}] {dev}")

    return audio_devices

if __name__ == "__main__":
    list_dshow_audio_devices()
