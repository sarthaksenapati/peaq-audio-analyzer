import os
import time
import threading
from adb_controller import check_adb_connection, push_audio
from aux_recorder import AuxRecorder
from peaq_analyzer import run_peaq_analysis
from batch_processor import BatchProcessor
from audio_utils import get_audio_duration
from file_manager import select_audio_files
from playback_options import choose_playback_method
import matplotlib
matplotlib.use('Agg')  # Safe for threads and headless

def run_batch_mode():
    print("📦 Starting Batch Mode")
    print("=" * 50)

    if not check_adb_connection():
        print("❌ No ADB device connected.")
        return

    print("✅ ADB connection verified")

    audio_files = select_audio_files()
    if not audio_files:
        print("❌ No audio files selected.")
        return

    print(f"📁 Selected {len(audio_files)} audio file(s)")

    recorder = AuxRecorder()
    if not recorder.prompt_and_set_device():
        print("❌ Aborting: No valid AUX device selected.")
        return

    processor = BatchProcessor()
    os.makedirs("extracted_audio", exist_ok=True)
    os.makedirs(processor.graphs_folder, exist_ok=True)

    playback_func = choose_playback_method()
    total_start_time = time.time()
    analysis_thread = None

    try:
        for i, file_path in enumerate(audio_files):
            base_name = os.path.splitext(os.path.basename(file_path))[0]

            def push_and_record(path):
                duration = get_audio_duration(path)
                if duration is None or duration <= 0:
                    raise ValueError(f"Invalid audio duration: {duration}")
                print(f"📊 Audio duration: {duration:.2f}s")

                print("📤 Pushing audio to device...")
                push_audio(path)

                print("🎙️ Starting AUX recording...")
                recorder.start(path, lambda f: playback_func(f, on_kill_callback=recorder.stop))

                print("⏳ Waiting for AUX recording to complete...")
                recorder.stop()
                return path

            def run_analysis(input_path):
                output_clean = os.path.join("extracted_audio", f"{base_name}_clean.wav")
                if os.path.exists(output_clean):
                    os.remove(output_clean)

                print("🔧 Post-processing recording...")
                if not recorder.post_process(None, input_path, output_clean):
                    print("❌ Post-processing failed")
                    return
                if not os.path.exists(output_clean):
                    print(f"❌ Post-processed file not found: {output_clean}")
                    return

                print("📈 Running PEAQ analysis...")
                odg, quality = run_peaq_analysis(input_path, output_clean, processor.graphs_folder)
                if odg is None or quality is None:
                    print("❌ PEAQ analysis failed")
                    return

                graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")
                interruptions = len(getattr(recorder.tracker, 'interruptions', []))

                processor.add_result(
                    input_path, odg, quality,
                    time.time() - total_start_time,
                    interruptions,
                    graph_path=graph_path,
                    success=True
                )
                print(f"✅ Successfully processed: ODG={odg:.2f}, Quality={quality}")

            # Run this file
            input_path = push_and_record(file_path)

            if analysis_thread:
                analysis_thread.join()

            analysis_thread = threading.Thread(target=run_analysis, args=(input_path,))
            analysis_thread.start()

            if i + 1 < len(audio_files):
                next_file = audio_files[i + 1]
                next_push_thread = threading.Thread(target=push_audio, args=(next_file,))
                next_push_thread.start()
                next_push_thread.join()

        if analysis_thread:
            analysis_thread.join()

        print("✅ All files processed and analyzed.")

    except Exception as e:
        print(f"❌ Batch mode failed: {e}")

    total_time = time.time() - total_start_time
    print(f"\n{'=' * 50}")
    print("📊 BATCH PROCESSING COMPLETE")
    print(f"Total files: {len(audio_files)}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per file: {total_time / len(audio_files):.1f}s")

    try:
        processor.save_results_to_excel()
        print("✅ Results saved to Excel")
    except Exception as e:
        print(f"❌ Failed to save Excel results: {e}")

    processor.print_batch_summary()

if __name__ == "__main__":
    run_batch_mode()
