import subprocess
import os
import datetime
import re
import threading
import time

from audio_utils import get_audio_duration
from config import output_audio_dir

class AuxRecorder:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.output_file = None
        self.selected_device = None
        self.tracker = self
        self.interruptions = []
        self.ffmpeg_path = ffmpeg_path

    def list_dshow_audio_devices(self):
        print("🔍 Scanning for available audio input devices...\n")
        print(f"[DEBUG] Using ffmpeg at: {self.ffmpeg_path}")
        result = subprocess.run(
            [self.ffmpeg_path, "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
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

        original_duration = get_audio_duration(audio_file)
        buffer_seconds = 4.0  # Full raw buffer before/after
        total_duration = original_duration + buffer_seconds

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = os.path.join(output_audio_dir, f"aux_recording_{timestamp}.wav")

        print("\n🎙️ Starting recording before playback...")

        start_event = threading.Event()

        def record():
            print(f"🎧 Recording from '{self.selected_device}' for {total_duration:.2f} seconds...")
            print(f"[DEBUG] Using ffmpeg at: {self.ffmpeg_path}")
            start_event.wait()
            subprocess.run([
                self.ffmpeg_path,
                "-y",
                "-f", "dshow",
                "-i", f"audio={self.selected_device}",
                "-t", str(total_duration),
                self.output_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        record_thread = threading.Thread(target=record)
        record_thread.start()

        time.sleep(0.1)  # Let recording thread prepare
        start_event.set()  # Begin recording now
        play_func(audio_file)  # Trigger playback now (or after delay, up to mode)

        record_thread.join()

    def stop(self):
        print("⏳ Waiting for FFmpeg to finish (handled automatically)...")

    def post_process(self, video_path, original_audio, output_path):
        if not os.path.exists(self.output_file):
            print("❌ AUX recording file not found.")
            return False

        try:
            if os.path.exists(output_path):
                os.remove(output_path)

            print("✂️ Precisely trimming based on known offset and duration...")
            temp_trimmed = self.output_file.replace(".wav", "_trimmed.wav")

            # Exact timing
            delay_before_play = 3.0  # seconds to skip at beginning
            duration = get_audio_duration(original_audio)

            print(f"[DEBUG] Using ffmpeg at: {self.ffmpeg_path}")
            trim_result = subprocess.run([
                self.ffmpeg_path,
                "-y",
                "-i", self.output_file,
                "-ss", str(delay_before_play),
                "-t", f"{duration:.2f}",
                "-c:a", "pcm_s16le",  # ensure uncompressed WAV
                temp_trimmed
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if trim_result.returncode == 0:
                os.remove(self.output_file)
                os.rename(temp_trimmed, output_path)
                print(f"✅ AUX recording trimmed and saved: {output_path}")
                return True
            else:
                print("⚠️ Trimming failed, using raw recording...")
                os.rename(self.output_file, output_path)
                if os.path.exists(temp_trimmed):
                    os.remove(temp_trimmed)
                return True

        except Exception as e:
            print(f"❌ Failed to process AUX recording to {output_path}")
            print("Error:", e)
            return False
