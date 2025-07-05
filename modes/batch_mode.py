import time
import os
from adb_controller import check_adb_connection, push_audio, list_recordings, pull_recording
from flawless_recorder import FlawlessRecorder
from peaq_analyzer import run_peaq_analysis
from batch_processor import BatchProcessor
from audio_utils import get_audio_duration
from file_manager import select_audio_files

def play_audio(file_path):
    filename = os.path.basename(file_path)
    device_path = f"/sdcard/{filename}"
    os.system(f'adb shell am start -a android.intent.action.VIEW -d file://{device_path} -t audio/wav')

def run_batch_mode():
    print("📦 Batch Mode")
    if not check_adb_connection():
        print("❌ No ADB device connected.")
        return

    audio_files = select_audio_files()
    recorder = FlawlessRecorder()
    processor = BatchProcessor()

    for file in audio_files:
        start = time.time()
        try:
            duration = get_audio_duration(file)
            push_audio(file)

            before = list_recordings()
            recorder.start(file, play_audio)
            time.sleep(duration + 2)
            recorder.stop()

            time.sleep(3)
            after = list_recordings()
            new_files = sorted(set(after) - set(before))

            if not new_files:
                print("⚠️ No difference detected in file list. Retrying...")
                time.sleep(2)
                after = list_recordings()
                new_files = sorted(set(after) - set(before))
                if not new_files:
                    print(f"❌ Skipping {file} - recording not found.")
                    continue

            new_file = new_files[-1]
            pulled_file = pull_recording(new_file)

            output_clean = os.path.join("extracted_audio", f"{os.path.splitext(os.path.basename(file))[0]}_clean.wav")

            if recorder.post_process(pulled_file, file, output_clean):
                # Run PEAQ and get graph saved in correct folder
                odg, quality = run_peaq_analysis(file, output_clean, processor.graphs_folder)

                graph_path = os.path.join(processor.graphs_folder, f"{os.path.splitext(os.path.basename(file))[0]}.png")

                processor.add_result(
                    file,
                    odg,
                    quality,
                    time.time() - start,
                    len(recorder.tracker.interruptions),
                    graph_path=graph_path
                )

        except Exception as e:
            processor.add_result(
                file,
                None,
                None,
                time.time() - start,
                None,
                None,
                success=False,
                error_message=str(e)
            )

    processor.save_results_to_excel()
    processor.print_batch_summary()
