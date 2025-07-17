import subprocess
import os
import datetime
import re

def list_dshow_audio_devices(ffmpeg_path="ffmpeg"):
    print("🔍 Scanning for available audio input devices...\n")
    result = subprocess.run(
        [ffmpeg_path, "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    devices_output = result.stderr  # FFmpeg writes this info to stderr
    device_lines = [line.strip() for line in devices_output.splitlines() if "audio devices" in line or '"' in line]


    # Extract device names
    audio_devices = []
    for line in device_lines:
        match = re.search(r'"([^"]+)"', line)
        if match:
            audio_devices.append(match.group(1))
    
    return audio_devices

def record_aux_audio(duration=15, ffmpeg_path="ffmpeg"):
    devices = list_dshow_audio_devices(ffmpeg_path)
    
    if not devices:
        print("❌ No audio input devices found. Make sure something like 'Stereo Mix' or 'Line In' is enabled.")
        return
    
    print("\n🎤 Available Audio Devices:")
    for i, dev in enumerate(devices):
        print(f"[{i}] {dev}")
    
    try:
        index = int(input("\nSelect device index to use: "))
        selected_device = devices[index]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        return
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"aux_recording_{timestamp}.wav"
    
    print(f"\n🎧 Recording from '{selected_device}' for {duration} seconds...")

    try:
        subprocess.run([
            ffmpeg_path,
            "-y",
            "-f", "dshow",
            "-i", f"audio={selected_device}",
            "-t", str(duration),
            output_filename
        ], check=True)
        
        print(f"✅ Recording complete. Saved as: {output_filename}")
    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg failed to record.")
        print("Error details:", e)

if __name__ == "__main__":
    # Optionally hardcode ffmpeg_path if not in PATH
    ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
    record_aux_audio(duration=15, ffmpeg_path=ffmpeg_path)
