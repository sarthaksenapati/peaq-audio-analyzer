# excel_mode.py
import os
import time
import pandas as pd
from tkinter import filedialog
from batch_processor import BatchProcessor
from flawless_recorder import FlawlessRecorder
from adb_controller import check_adb_connection, list_recordings, pull_recording
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis
from config import output_audio_dir, device_audio_dir
import subprocess
import urllib.parse

def run_excel_based_testing_mode():
    print("📊 Excel-Driven Mode")

    if not check_adb_connection():
        return

    excel_path = filedialog.askopenfilename(
        title="Select Excel File", filetypes=[("Excel Files", "*.xlsx *.xls")]
    )
    if not excel_path:
        print("❌ No Excel file selected.")
        return

    folder_path = filedialog.askdirectory(title="Select Folder Containing Audio Files")
    if not folder_path:
        print("❌ No folder selected.")
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

        processor = BatchProcessor()
        recorder = FlawlessRecorder()

        print(f"📁 Selected Excel: {os.path.basename(excel_path)}")
        print(f"📁 Folder: {folder_path}")
        print(f"🎵 Total Files: {len(local_audio_files)}")

        # Reset device audio dir
        subprocess.run(["adb", "shell", f"rm -rf {device_audio_dir}"], capture_output=True)
        subprocess.run(["adb", "shell", f"mkdir -p {device_audio_dir}"], capture_output=True)

        for file in local_audio_files:
            subprocess.run(["adb", "push", file, device_audio_dir], capture_output=True)

        for audio_file in local_audio_files:
            start_time = time.time()
            base_name = os.path.splitext(os.path.basename(audio_file))[0]
            try:
                duration = get_audio_duration(audio_file)
                device_file_path = f"{device_audio_dir}/{os.path.basename(audio_file)}"

                before = list_recordings()

                # Escape for URL
                escaped = urllib.parse.quote(device_file_path)
                audio_type = "audio/wav"
                if audio_file.lower().endswith(".mp3"):
                    audio_type = "audio/mpeg"
                elif audio_file.lower().endswith(".flac"):
                    audio_type = "audio/flac"

                # Start recording before playback
                recorder.start(audio_file, lambda x: None)
                time.sleep(1.5)

                subprocess.run([
                    "adb", "shell", "am", "start", "-a", "android.intent.action.VIEW",
                    "-d", f"file://{escaped}", "-t", audio_type
                ], capture_output=True, text=True)

                time.sleep(duration + 2)
                recorder.stop()
                time.sleep(4)

                after = list_recordings()
                new_files = list(set(after) - set(before))
                if not new_files:
                    raise RuntimeError("No new recording found.")

                newest = sorted(new_files)[-1]
                pulled = pull_recording(newest)

                # ✅ Save clean audio to extracted_audio/
                output_audio = os.path.join("extracted_audio", f"{base_name}_clean.wav")
                if not recorder.post_process(pulled, audio_file, output_audio):
                    raise RuntimeError("Post-processing failed.")

                # ✅ Run PEAQ and plot to graphs folder
                odg, quality = run_peaq_analysis(audio_file, output_audio, processor.graphs_folder)
                if odg is None:
                    raise RuntimeError("PEAQ analysis failed.")

                graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")

                # ✅ Save to Excel inside batch_results/batch_xxxx
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

    except Exception as e:
        print(f"❌ Failed to run Excel-driven test: {e}")
