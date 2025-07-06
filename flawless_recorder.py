import time
import os
from screen_recorder import start_recording_az, stop_and_save_recording_az
from audio_utils import get_audio_duration, trim_audio_with_ffmpeg
from config import output_audio_dir

class FlawlessRecorder:
    def __init__(self):
        self.tracker = self  # For compatibility with batch_mode.py
        self.interruptions = []  # Initialize interruptions list

    def start(self, audio_file, play_func):
        start_recording_az()
        time.sleep(2)
        play_func(audio_file)

    def stop(self):
        stop_and_save_recording_az()

    def post_process(self, video_path, original_audio, output_path):
        duration = get_audio_duration(original_audio)
        print(f"🎞️ Trimming video {video_path} to {duration:.2f}s of audio...")
        
        # Fixed: Use actual duration (not truncated) and configurable start offset
        start_offset = 4.0  # You can adjust this based on your setup
        
        # Ensure we don't trim more than the video length
        video_duration = get_video_duration(video_path)  # We'll need this function
        if video_duration is None:
            print("⚠️ Could not determine video duration, using original duration")
            trim_duration = duration
        else:
            # Account for start offset
            available_duration = video_duration - start_offset
            trim_duration = min(duration, available_duration)
            if trim_duration != duration:
                print(f"⚠️ Video too short, trimming to {trim_duration:.2f}s instead of {duration:.2f}s")
        
        # Use floating point duration (not int!)
        success = trim_audio_with_ffmpeg(video_path, output_path, start_offset, trim_duration)

        if not success or not os.path.exists(output_path):
            print("❌ Trim failed or output file not created.")
            return False

        final_dur = get_audio_duration(output_path)
        if final_dur < 0.2:
            print(f"⚠️ Trimmed audio is too short: {final_dur:.2f}s")
            return False

        print(f"✅ Clean audio saved: {output_path} ({final_dur:.2f}s)")
        
        # Check for significant duration mismatch
        duration_diff = abs(final_dur - duration)
        if duration_diff > 0.5:  # More than 0.5 second difference
            print(f"⚠️ Warning: Duration mismatch of {duration_diff:.2f}s (expected: {duration:.2f}s, got: {final_dur:.2f}s)")
        
        return True


def get_video_duration(video_path):
    """Get duration of video file using ffprobe"""
    import subprocess
    try:
        result = subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", video_path
        ], capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception as e:
        print(f"⚠️ Could not get video duration: {e}")
    return None