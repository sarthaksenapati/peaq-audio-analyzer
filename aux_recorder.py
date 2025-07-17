import subprocess
import os
import datetime
import re
from audio_utils import get_audio_duration
from config import output_audio_dir

class AuxRecorder:
    def __init__(self):
        self.output_file = None
        self.selected_device = None
        self.tracker = self
        self.interruptions = []

    def list_dshow_audio_devices(self, ffmpeg_path="ffmpeg"):
        print("🔍 Scanning for available audio input devices...\n")
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
        
        return audio_devices

    def prompt_and_set_device(self):
        devices = self.list_dshow_audio_devices()
        if not devices:
            print("❌ No audio input devices found. Make sure 'Stereo Mix' or 'Line In' is enabled.")
            return False

        print("\n🎤 Available Audio Devices:")
        for i, dev in enumerate(devices):
            print(f"[{i}] {dev}")

        try:
            index = int(input("\nSelect device index to use: "))
            self.selected_device = devices[index]
            return True
        except (ValueError, IndexError):
            print("❌ Invalid selection.")
            return False

    def start(self, audio_file, play_func):
        if not self.selected_device:
            print("❌ No input device selected. Call prompt_and_set_device() first.")
            return

        duration = get_audio_duration(audio_file)
        duration += 1.0  # Add 1 second buffer

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = os.path.join(output_audio_dir, f"aux_recording_{timestamp}.wav")

        print(f"\n🎧 Recording from '{self.selected_device}' for {duration:.2f} seconds...")
        try:
            subprocess.Popen([
                "ffmpeg",
                "-y",
                "-f", "dshow",
                "-i", f"audio={self.selected_device}",
                "-t", str(duration),
                self.output_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print("❌ Failed to start FFmpeg recording.")
            print("Error:", e)
            return

        play_func(audio_file)

    def stop(self):
        print("⏳ Waiting for FFmpeg to finish (handled automatically)...")

    def post_process(self, video_path, original_audio, output_path):
        if not os.path.exists(self.output_file):
            print("❌ AUX recording file not found.")
            return False

        try:
            if os.path.exists(output_path):
                os.remove(output_path)  # 💥 Remove old output first
            os.rename(self.output_file, output_path)
            print(f"✅ AUX recording saved: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to move AUX recording to {output_path}")
            print("Error:", e)
            return False

