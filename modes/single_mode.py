# modes/single_mode.py

import time
import os
from adb_controller import check_adb_connection, push_audio, list_recordings, pull_recording
from flawless_recorder import FlawlessRecorder
from peaq_analyzer import run_peaq_analysis
from config import output_audio_dir
from audio_utils import get_audio_duration
from file_manager import select_audio_files
import os
os.makedirs("./graphs", exist_ok=True)


def play_audio(file_path):
    filename = os.path.basename(file_path)
    device_path = f"/sdcard/{filename}"
    os.system(f'adb shell am start -a android.intent.action.VIEW -d file://{device_path} -t audio/wav')

def run_single_mode():
    print("🎧 Select an audio file to push and record...")
    if not check_adb_connection():
        print("❌ No ADB device connected.")
        return

    audio_file = select_audio_files()[0]
    duration = get_audio_duration(audio_file)
    print(f"⏱️ Duration: {duration:.2f} seconds")

    push_audio(audio_file)

    recorder = FlawlessRecorder()
    before = list_recordings()

    recorder.start(audio_file, play_audio)
    time.sleep(duration + 2)
    recorder.stop()

    time.sleep(3)  # Let AZ Screen Recorder save the file
    after = list_recordings()
    new_files = sorted(set(after) - set(before))

    if not new_files:
        print("⚠️ No difference detected in file list. Retrying...")
        time.sleep(2)
        after = list_recordings()
        new_files = sorted(set(after) - set(before))
        if not new_files:
            print("❌ Could not detect new recording. Please check manually.")
            return

    new_file = new_files[-1]
    pulled_file = pull_recording(new_file)

    output_clean = os.path.join(output_audio_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_clean.wav")
    if recorder.post_process(pulled_file, audio_file, output_clean):
        odg, quality = run_peaq_analysis(audio_file, output_clean, "./graphs")

        print(f"\n🎯 ODG: {odg:.2f} | Quality: {quality}")
