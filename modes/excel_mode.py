import os
import time
import pandas as pd
import subprocess
from batch_processor import BatchProcessor
from flawless_recorder import FlawlessRecorder
from aux_recorder import AuxRecorder
from adb_controller import check_adb_connection, list_recordings, pull_recording
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis
from config import output_audio_dir, device_audio_dir
from playback_options import choose_playback_method


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

        # 🆕 Ask user for recording method
        print("\n🎙️ Select recording method:")
        print("  [1] AZ Screen Recorder (Phone)")
        print("  [2] AUX Cable Recording (PC)")
        choice = input("> ").strip()

        if choice == '2':
            recorder = AuxRecorder()
            if not recorder.prompt_and_set_device():
                print("❌ Aborting: No valid AUX device selected.")
                return
        else:
            recorder = FlawlessRecorder()

        is_az = isinstance(recorder, FlawlessRecorder)
        processor = BatchProcessor()

        print(f"📁 Using Excel: {os.path.basename(excel_path)}")
        print(f"📁 Audio Folder: {folder_path}")
        print(f"🎵 Total Files: {len(local_audio_files)}")

        playback_func = choose_playback_method()

        if is_az:
            subprocess.run(["adb", "shell", f"rm -rf {device_audio_dir}"], capture_output=True)
            subprocess.run(["adb", "shell", f"mkdir -p {device_audio_dir}"], capture_output=True)
            for file in local_audio_files:
                subprocess.run(["adb", "push", file, device_audio_dir], capture_output=True)

        for audio_file in local_audio_files:
            start_time = time.time()
            base_name = os.path.splitext(os.path.basename(audio_file))[0]
            output_audio = os.path.join("extracted_audio", f"{base_name}_clean.wav")
            os.makedirs("extracted_audio", exist_ok=True)

            try:
                duration = get_audio_duration(audio_file)

                if is_az:
                    before = list_recordings()

                print("🎙️ Starting recording with Files app sync...")
                recorder.start(audio_file, lambda f: playback_func(f, on_kill_callback=recorder.stop))

                if not is_az:
                    print("⏳ Waiting for AUX recording to complete...")
                    recorder.stop()

                    # ✅ Handle existing file conflict
                    if os.path.exists(output_audio):
                        os.remove(output_audio)

                    if not recorder.post_process(None, audio_file, output_audio):
                        raise RuntimeError("Post-processing failed (AUX mode)")

                    odg, quality = run_peaq_analysis(audio_file, output_audio, processor.graphs_folder)
                    graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")
                    interruptions = len(getattr(recorder.tracker, 'interruptions', []))

                    processor.add_result(audio_file, odg, quality, time.time() - start_time,
                                         interruptions, graph_path)
                    processor.save_results_to_excel()
                    continue

                # AZ screen recorder flow
                print("💾 Waiting for recording to be saved...")
                new_files = wait_for_new_recording(before)

                if not new_files:
                    raise RuntimeError("No new recording found.")

                latest = sorted(new_files)[-1]
                pulled = pull_recording(latest)

                # ✅ Handle existing file conflict
                if os.path.exists(output_audio):
                    os.remove(output_audio)

                if not recorder.post_process(pulled, audio_file, output_audio):
                    raise RuntimeError("Post-processing failed.")

                odg, quality = run_peaq_analysis(audio_file, output_audio, processor.graphs_folder)
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
