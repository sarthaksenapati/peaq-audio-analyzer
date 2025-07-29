import time
import os
import subprocess
import urllib.parse
from adb_controller import check_adb_connection, push_audio
from aux_recorder import AuxRecorder  # Only AUX recorder now
from peaq_analyzer import run_peaq_analysis
from config import output_audio_dir
from audio_utils import get_audio_duration
from file_manager import select_audio_files
from playback_options import choose_playback_method

os.makedirs("results/single", exist_ok=True)

def run_single_mode():
    print("🎧 Select an audio file to push and record...")
    if not check_adb_connection():
        print("❌ No ADB device connected.")
        return

    audio_file = select_audio_files()[0]
    duration = get_audio_duration(audio_file)
    print(f"⏱️ Duration: {duration:.2f} seconds")

    push_audio(audio_file)

    recorder = AuxRecorder()
    recorder.prompt_and_set_device()

    play_func = choose_playback_method()
    print("🎙️ Starting recording...")
    recorder.start(audio_file, play_func)

    print("⏳ Waiting for AUX recording to complete...")
    recorder.stop()

    output_clean = os.path.join(output_audio_dir, f"{os.path.splitext(os.path.basename(audio_file))[0]}_clean.wav")
    if recorder.post_process(None, audio_file, output_clean):
        odg, quality = run_peaq_analysis(audio_file, output_clean, "results/single")
        print(f"\n🎯 ODG: {odg:.2f} | Quality: {quality}")
