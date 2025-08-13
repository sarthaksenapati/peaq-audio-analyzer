import os
import time
import threading
import pandas as pd
import subprocess
from tkinter import filedialog, Tk
from batch_processor import BatchProcessor
from aux_recorder import AuxRecorder
from adb_controller import check_adb_connection, push_audio
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis
from config import output_audio_dir
from playback_options import choose_playback_method
import matplotlib

matplotlib.use('Agg')  # ✅ Safe for threads; no GUI dependencies


def run_excel_based_testing_mode():
    print("📊 Excel-Driven Mode")

    if not check_adb_connection():
        return

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(root_dir, "testcase.xlsx")

    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found at {excel_path}")
        return

    print("📂 Please select the folder containing audio files...")
    Tk().withdraw()
    folder_path = filedialog.askdirectory(title="Select Audio Files Folder")

    if not folder_path or not os.path.exists(folder_path):
        print("❌ No folder selected or folder does not exist. Aborting.")
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
            print("❌ No valid audio files found in the selected folder.")
            return

        recorder = AuxRecorder()
        if not recorder.prompt_and_set_device():
            print("❌ Aborting: No valid AUX device selected.")
            return

        processor = BatchProcessor()

        print(f"📁 Using Excel: {os.path.basename(excel_path)}")
        print(f"📁 Audio Folder: {folder_path}")
        print(f"🎵 Total Files: {len(local_audio_files)}")

        playback_func = choose_playback_method()
        os.makedirs("extracted_audio", exist_ok=True)
        os.makedirs("temp_converted", exist_ok=True)

        total_start_time = time.time()
        analysis_thread = None

        for i, audio_file in enumerate(local_audio_files):
            base_name = os.path.basename(audio_file)  # Keeps extension like song.mp3


            def push_and_record(path):
                audio_input = path  # Accept all file formats; no conversion
                duration = get_audio_duration(audio_input)
                push_audio(audio_input)

                print("🎙️ Starting AUX recording with Files app sync...")
                recorder.start(audio_input, lambda f: playback_func(f, on_kill_callback=recorder.stop))

                print("⏳ Waiting for AUX recording to complete...")
                recorder.stop()
                return audio_input

            def run_analysis(audio_input, base_name):
                output_audio = os.path.join("extracted_audio", f"{base_name}_clean.wav")
                if os.path.exists(output_audio):
                    os.remove(output_audio)
                if not recorder.post_process(None, audio_input, output_audio):
                    print("❌ Post-processing failed (AUX mode)")
                    return
                odg, quality = run_peaq_analysis(audio_input, output_audio, processor.graphs_folder)
                graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")
                interruptions = len(getattr(recorder.tracker, 'interruptions', []))
                processor.add_result(base_name, odg, quality, time.time() - total_start_time,
                                     interruptions, graph_path)
                processor.save_results_to_excel()
                print(f"✅ Successfully processed: ODG={odg:.2f}, Quality={quality}")

            audio_input = push_and_record(audio_file)

            if analysis_thread:
                analysis_thread.join()

            # ✅ Pass base_name explicitly to avoid overwriting in threads
            analysis_thread = threading.Thread(target=run_analysis, args=(audio_input, base_name))
            analysis_thread.start()

            # Optional: Pre-push next file
            if i + 1 < len(local_audio_files):
                next_file = local_audio_files[i + 1]
                threading.Thread(target=push_audio, args=(next_file,)).start()

        if analysis_thread:
            analysis_thread.join()

        processor.save_results_to_excel()
        processor.print_batch_summary()

    except Exception as e:
        print(f"❌ Failed to run Excel-driven test: {e}")
