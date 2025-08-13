import os
import time
import threading
import subprocess
from batch_processor import BatchProcessor
from aux_recorder import AuxRecorder
from adb_controller import check_adb_connection, push_audio
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis
from playback_options import choose_playback_method
import matplotlib
matplotlib.use('Agg')  # ✅ Safe for threads; no GUI dependencies

def run_folder_push_batch_mode():
    print("🔀 Folder Push Batch Mode")

    if not check_adb_connection():
        return

    recorder = AuxRecorder()
    if not recorder.prompt_and_set_device():
        print("❌ Aborting: No valid AUX device selected.")
        return

    processor = BatchProcessor()
    folder_result = processor.select_folder_to_push()
    if not folder_result:
        print("❌ No folder selected.")
        return

    local_folder, audio_files = folder_result
    print(f"📁 Selected folder: {local_folder} with {len(audio_files)} audio files.")

    if not audio_files:
        print("❌ No audio files found in the selected folder.")
        return

    playback_func = choose_playback_method()
    os.makedirs("extracted_audio", exist_ok=True)
    os.makedirs("temp_converted", exist_ok=True)

    total_start_time = time.time()
    analysis_thread = None

    for i, audio_file in enumerate(audio_files):
        def push_and_record(path):
            audio_input = path  # No conversion

            duration = get_audio_duration(audio_input)
            push_audio(audio_input)

            print("🎙️ Starting recording with Files app sync...")
            recorder.start(audio_input, lambda f: playback_func(f, on_kill_callback=recorder.stop))

            print("⏳ Waiting for AUX recording to complete...")
            recorder.stop()
            return audio_input

        def run_analysis(audio_input):
            base_name = os.path.basename(audio_input)
            clean_name = os.path.splitext(base_name)[0]
            output_clean = os.path.join("extracted_audio", f"{clean_name}_clean.wav")
            if os.path.exists(output_clean):
                os.remove(output_clean)
            if not recorder.post_process(None, audio_input, output_clean):
                print("❌ Post-processing failed.")
                return
            odg, quality = run_peaq_analysis(audio_input, output_clean, processor.graphs_folder)
            if odg is None:
                print("❌ PEAQ analysis failed.")
                return
            graph_path = os.path.join(processor.graphs_folder, f"{clean_name}.png")
            interruptions = len(getattr(recorder.tracker, 'interruptions', []))
            processor.add_result(
                base_name, odg, quality,
                time.time() - total_start_time,
                interruptions,
                graph_path
            )
            processor.save_results_to_excel()
            print(f"✅ Successfully processed: ODG={odg:.2f}, Quality={quality}")

        audio_input = push_and_record(audio_file)

        if analysis_thread:
            analysis_thread.join()

        analysis_thread = threading.Thread(target=run_analysis, args=(audio_input,))
        analysis_thread.start()

        if i + 1 < len(audio_files):
            next_file = audio_files[i + 1]
            next_push_thread = threading.Thread(target=push_audio, args=(next_file,))
            next_push_thread.start()
            next_push_thread.join()

    if analysis_thread:
        analysis_thread.join()

    processor.save_results_to_excel()
    processor.print_batch_summary()
