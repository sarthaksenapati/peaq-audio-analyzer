# modes/folder_push_mode.py

import os, time, urllib.parse, subprocess
from batch_processor import BatchProcessor
from flawless_recorder import FlawlessRecorder
from adb_controller import check_adb_connection, list_recordings, pull_recording
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis

def run_folder_push_batch_mode():
    print("🌀 Folder Push Batch Mode")

    if not check_adb_connection():
        return

    processor = BatchProcessor()
    recorder = FlawlessRecorder()
    
    folder_result = processor.select_folder_to_push()
    if not folder_result:
        print("❌ No folder selected.")
        return

    local_folder, audio_files = folder_result

    print(f"📁 Selected folder: {local_folder} with {len(audio_files)} WAV files.")

    if not audio_files:
        print("❌ No .wav files found in the selected folder.")
        return

    for audio_file in audio_files:
        start_time = time.time()
        base_name = os.path.splitext(os.path.basename(audio_file))[0]

        try:
            # Push current file to device
            push_result = subprocess.run(["adb", "push", audio_file, "/sdcard/"], capture_output=True)
            if push_result.returncode != 0:
                raise RuntimeError(f"Failed to push file: {audio_file}")

            duration = get_audio_duration(audio_file)
            filename = os.path.basename(audio_file)
            device_file_path = f"/sdcard/{filename}"

            before = list_recordings()

            escaped = urllib.parse.quote(device_file_path)
            audio_type = "audio/wav"
            if filename.lower().endswith('.mp3'):
                audio_type = "audio/mpeg"
            elif filename.lower().endswith('.flac'):
                audio_type = "audio/flac"

            def on_start(_):
                time.sleep(1.2)
                subprocess.run([
                    "adb", "shell", "am", "start", "-a", "android.intent.action.VIEW",
                    "-d", f"file://{escaped}", "-t", audio_type
                ], capture_output=True, text=True)

            recorder.start(audio_file, on_start)
            time.sleep(duration + 3.5)
            recorder.stop()
            time.sleep(4)

            after = list_recordings()
            new_files = list(set(after) - set(before))
            if not new_files:
                raise RuntimeError("No new recording found.")

            newest = sorted(new_files)[-1]
            pulled = pull_recording(newest)

            # ✅ Save clean audio to ./extracted_audio/
            output_audio = os.path.join("extracted_audio", f"{base_name}_clean.wav")
            if not recorder.post_process(pulled, audio_file, output_audio):
                raise RuntimeError("Post-processing failed.")

            # ✅ Save graph and ODG to batch_results
            odg, quality = run_peaq_analysis(audio_file, output_audio, processor.graphs_folder)
            if odg is None:
                raise RuntimeError("PEAQ analysis failed.")

            graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")

            processor.add_result(
                audio_file, odg, quality,
                time.time() - start_time,
                0,
                graph_path
            )
            processor.save_results_to_excel()

        except Exception as e:
            processor.add_result(audio_file, None, None, time.time() - start_time,
                                 None, None, success=False, error_message=str(e))

    processor.save_results_to_excel()
    processor.print_batch_summary()
