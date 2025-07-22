import os
import time
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


def run_excel_based_testing_mode():
    print("📊 Excel-Driven Mode")

    if not check_adb_connection():
        return

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(root_dir, "testcase.xlsx")

    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found at {excel_path}")
        return

    # ✅ Let user select audio folder via Tkinter
    print("📂 Please select the folder containing audio files...")
    Tk().withdraw()  # Hide the main Tkinter window
    folder_path = filedialog.askdirectory(title="Select Audio Files Folder")

    if not folder_path:
        print("❌ No folder selected. Aborting.")
        return

    if not os.path.exists(folder_path):
        print(f"❌ Selected folder does not exist: {folder_path}")
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

        # ✅ AUX recording only
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

        for audio_file in local_audio_files:
            start_time = time.time()
            base_name = os.path.splitext(os.path.basename(audio_file))[0]

            try:
                # 🔁 Convert if needed
                if not audio_file.lower().endswith(".wav"):
                    converted_path = os.path.join("temp_converted", f"{base_name}.wav")
                    subprocess.run([
                        "ffmpeg", "-y", "-i", audio_file,
                        "-ar", "44100", "-ac", "2", converted_path
                    ], capture_output=True)
                    audio_input = converted_path
                else:
                    audio_input = audio_file

                duration = get_audio_duration(audio_input)
                output_audio = os.path.join("extracted_audio", f"{base_name}_clean.wav")

                push_audio(audio_input)

                print("🎙️ Starting AUX recording with Files app sync...")
                recorder.start(audio_input, lambda f: playback_func(f, on_kill_callback=recorder.stop))

                print("⏳ Waiting for AUX recording to complete...")
                recorder.stop()

                if os.path.exists(output_audio):
                    os.remove(output_audio)

                if not recorder.post_process(None, audio_input, output_audio):
                    raise RuntimeError("Post-processing failed (AUX mode)")

                odg, quality = run_peaq_analysis(audio_input, output_audio, processor.graphs_folder)
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
