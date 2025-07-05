import time
import os
from screen_recorder import start_recording_az, stop_and_save_recording_az
from audio_utils import get_audio_duration, trim_audio_with_ffmpeg
from config import output_audio_dir

class FlawlessRecorder:
    def __init__(self):
        pass

    def start(self, audio_file, play_func):
        start_recording_az()
        time.sleep(2)
        play_func(audio_file)

    def stop(self):
        stop_and_save_recording_az()

    def post_process(self, video_path, original_audio, output_path):
        duration = get_audio_duration(original_audio)
        print(f"🎞️ Trimming video {video_path} to {duration:.2f}s of audio...")
        success = trim_audio_with_ffmpeg(video_path, output_path, 4, int(duration))

        if not success or not os.path.exists(output_path):
            print("❌ Trim failed or output file not created.")
            return False

        final_dur = get_audio_duration(output_path)
        if final_dur < 0.2:
            print(f"⚠️ Trimmed audio is too short: {final_dur:.2f}s")
            return False

        print(f"✅ Clean audio saved: {output_path} ({final_dur:.2f}s)")
        return True
