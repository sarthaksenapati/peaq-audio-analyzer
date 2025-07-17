import os, time, subprocess
from batch_processor import BatchProcessor
from flawless_recorder import FlawlessRecorder
from aux_recorder import AuxRecorder
from adb_controller import check_adb_connection, list_recordings, pull_recording
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis
from playback_options import choose_playback_method


def run_folder_push_batch_mode():
    print("🌀 Folder Push Batch Mode")

    if not check_adb_connection():
        return

    processor = BatchProcessor()

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

    folder_result = processor.select_folder_to_push()
    if not folder_result:
        print("❌ No folder selected.")
        return

    local_folder, audio_files = folder_result
    print(f"📁 Selected folder: {local_folder} with {len(audio_files)} WAV files.")

    if not audio_files:
        print("❌ No .wav files found in the selected folder.")
        return

    playback_func = choose_playback_method()

    for audio_file in audio_files:
        start_time = time.time()
        base_name = os.path.splitext(os.path.basename(audio_file))[0]

        try:
            duration = get_audio_duration(audio_file)
            is_az = isinstance(recorder, FlawlessRecorder)

            if is_az:
                before = list_recordings()

            print("🎙️ Starting recording with Files app sync...")
            recorder.start(audio_file, lambda f: playback_func(f, on_kill_callback=recorder.stop))

            if is_az:
                print("💾 Waiting for recording to be saved...")
                for attempt in range(3):
                    time.sleep(2)
                    after = list_recordings()
                    new_files = list(set(after) - set(before))
                    if new_files:
                        break
                    print(f"⏳ Waiting for recording... attempt {attempt + 1}")
                else:
                    raise RuntimeError("No new recording found.")
                newest = sorted(new_files)[-1]
                pulled = pull_recording(newest)
            else:
                print("⏳ Waiting for AUX recording to complete...")
                recorder.stop()
                pulled = None  # Not needed for AUX

            output_clean = os.path.join("extracted_audio", f"{base_name}_clean.wav")
            os.makedirs("extracted_audio", exist_ok=True)

            if os.path.exists(output_clean):
                os.remove(output_clean)

            if not recorder.post_process(pulled, audio_file, output_clean):
                raise RuntimeError("Post-processing failed.")

            odg, quality = run_peaq_analysis(audio_file, output_clean, processor.graphs_folder)
            if odg is None:
                raise RuntimeError("PEAQ analysis failed.")

            graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")
            interruptions = len(getattr(recorder.tracker, 'interruptions', []))

            processor.add_result(
                audio_file, odg, quality,
                time.time() - start_time,
                interruptions,
                graph_path
            )
            processor.save_results_to_excel()

        except Exception as e:
            processor.add_result(audio_file, None, None, time.time() - start_time,
                                 None, None, success=False, error_message=str(e))

    processor.save_results_to_excel()
    processor.print_batch_summary()
