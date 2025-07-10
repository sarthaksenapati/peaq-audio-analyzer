# excel_mode.py
import os
import time
import pandas as pd
import subprocess
import urllib.parse
from tkinter import filedialog
from batch_processor import BatchProcessor
from flawless_recorder import FlawlessRecorder
from adb_controller import check_adb_connection, list_recordings, pull_recording
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis
from config import output_audio_dir, device_audio_dir
from playback_options import choose_playback_method  # ✅ New: ask user for playback method


def wait_for_new_recording(before_files, max_retries=3, retry_delay=2):
    for attempt in range(max_retries):
        time.sleep(retry_delay)
        after_files = list_recordings()
        new_files = sorted(set(after_files) - set(before_files))

        if new_files:
            print(f"✅ Found {len(new_files)} new recording(s) after {attempt + 1} attempt(s)")
            return new_files

        print(f"⏳ Attempt {attempt + 1}/{max_retries}: No new recordings found, retrying...")

    return []


def run_excel_based_testing_mode():
    print("📊 Excel-Driven Mode")

    if not check_adb_connection():
        return

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(root_dir, "testcase.xlsx")
    folder_path = os.path.join(root_dir, "audio_files")

    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found at {excel_path}")
        return

    if not os.path.exists(folder_path):
        print(f"❌ Audio folder not found at {folder_path}")
        return

    try:
        df = pd.read_excel(excel_path)
        if 'Audio File' not in df.columns:
            print("❌ Excel must contain 'Audio File' column.")
            return

        file_list = df['Audio File'].dropna().astype(str).tolist()
        local_audio_files = [
            os.path.join(folder_path, f)
            for f in file_list
            if os.path.exists(os.path.join(folder_path, f))
        ]

        if not local_audio_files:
            print("❌ No valid audio files found in the audio folder.")
            return

        processor = BatchProcessor()
        recorder = FlawlessRecorder()

        print(f"📁 Using Excel: {os.path.basename(excel_path)}")
        print(f"📁 Audio Folder: {folder_path}")
        print(f"🎵 Total Files: {len(local_audio_files)}")

        playback_func = choose_playback_method()

        subprocess.run(["adb", "shell", f"rm -rf {device_audio_dir}"], capture_output=True)
        subprocess.run(["adb", "shell", f"mkdir -p {device_audio_dir}"], capture_output=True)

        for file in local_audio_files:
            subprocess.run(["adb", "push", file, device_audio_dir], capture_output=True)

        for audio_file in local_audio_files:
            start_time = time.time()
            base_name = os.path.splitext(os.path.basename(audio_file))[0]

            try:
                duration = get_audio_duration(audio_file)
                before = list_recordings()

                print("🎙️ Starting recording...")
                recorder.start(audio_file, playback_func)

                wait_time = duration 
                print(f"⏱️ Waiting {wait_time:.1f}s for playback...")
                time.sleep(0)

                print("⏹️ Stopping recording...")
                recorder.stop()

                print("💾 Waiting for recording to be saved...")
                new_files = wait_for_new_recording(before)

                if not new_files:
                    raise RuntimeError("No new recording found.")

                latest = sorted(new_files)[-1]
                pulled = pull_recording(latest)

                output_audio = os.path.join("extracted_audio", f"{base_name}_clean.wav")
                if not recorder.post_process(pulled, audio_file, output_audio):
                    raise RuntimeError("Post-processing failed.")

                if not os.path.exists(output_audio):
                    raise RuntimeError("Expected trimmed output not found.")

                odg, quality = run_peaq_analysis(audio_file, output_audio, processor.graphs_folder)
                if odg is None:
                    raise RuntimeError("PEAQ analysis failed.")

                graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")
                interruptions = len(getattr(recorder.tracker, 'interruptions', []))

                processor.add_result(audio_file, odg, quality, time.time() - start_time,
                                     interruptions, graph_path)
                processor.save_results_to_excel()

            except Exception as e:
                processor.add_result(audio_file, None, None, time.time() - start_time,
                                     None, None, success=False, error_message=str(e))

        processor.save_results_to_excel()
        processor.print_batch_summary()

    except Exception as e:
        print(f"❌ Failed to run Excel-driven test: {e}")
