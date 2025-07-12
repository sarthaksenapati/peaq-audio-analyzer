import os, time, subprocess
from batch_processor import BatchProcessor
from flawless_recorder import FlawlessRecorder
from adb_controller import check_adb_connection, list_recordings, pull_recording
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis
from playback_options import choose_playback_method  # ✅ Unified playback control


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

    # ✅ Ask user which playback method to use
    playback_func = choose_playback_method()

    for audio_file in audio_files:
        start_time = time.time()
        base_name = os.path.splitext(os.path.basename(audio_file))[0]

        try:
            duration = get_audio_duration(audio_file)
            before = list_recordings()

            print("🎙️ Starting recording with Files app sync...")
            # ✅ Inject the stop function when Files app finishes
            recorder.start(audio_file, lambda f: playback_func(f, on_kill_callback=recorder.stop))

            print("💾 Waiting for recording to be saved...")
            for attempt in range(3):
                time.sleep(2)
                after = list_recordings()
                new_files = list(set(after) - set(before))
                if new_files:
                    break
                print(f"⏳ Waiting for recording... attempt {attempt+1}")
            else:
                raise RuntimeError("No new recording found.")

            newest = sorted(new_files)[-1]
            pulled = pull_recording(newest)

            output_audio = os.path.join("extracted_audio", f"{base_name}_clean.wav")
            if not recorder.post_process(pulled, audio_file, output_audio):
                raise RuntimeError("Post-processing failed.")

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
