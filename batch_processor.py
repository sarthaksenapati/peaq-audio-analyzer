import os
import pandas as pd
import numpy as np
from datetime import datetime
from config import batch_results_dir
import shutil
from config import device_audio_dir
import subprocess
import tkinter as tk
from tkinter import filedialog



class BatchProcessor:
    def __init__(self):
        self.results = []
        self.batch_folder = None
        self.graphs_folder = None
        self.excel_file = None
        self.setup_batch_folders()

    def setup_batch_folders(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.batch_folder = os.path.join(batch_results_dir, f"batch_{timestamp}")
        self.graphs_folder = os.path.join(self.batch_folder, "graphs")
        os.makedirs(self.batch_folder, exist_ok=True)
        os.makedirs(self.graphs_folder, exist_ok=True)
        self.excel_file = os.path.join(self.batch_folder, "batch_results.xlsx")

    def select_folder_to_push(self):
        """Use a GUI dialog to select a folder containing audio files."""
        try:
            import tkinter as tk
            from tkinter import filedialog
            tk.Tk().withdraw()
            folder = filedialog.askdirectory(title="Select Folder for Batch Push")
            if folder and os.path.exists(folder):
                wav_files = [f for f in os.listdir(folder) if f.endswith('.wav')]
                if not wav_files:
                    print("⚠️  Selected folder does not contain any .wav files.")
                    return None
                print(f"📁 Selected folder: {folder} with {len(wav_files)} WAV files.")
                return folder, [os.path.join(folder, f) for f in wav_files]
            else:
                print("❌ No folder selected or folder does not exist.")
                return None
        except Exception as e:
            print(f"❌ Error selecting folder: {e}")
            return None    

    def read_files_from_excel(self):
        """
        Asks user to select an Excel file and a folder.
        Returns: (excel_path, list of full audio paths to process)
        """
        try:
            tk.Tk().withdraw()
            excel_path = filedialog.askopenfilename(
                title="Select Excel File with Audio Filenames",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            if not excel_path or not os.path.exists(excel_path):
                print("❌ Excel file not selected or does not exist.")
                return None, None

            folder = filedialog.askdirectory(title="Select Folder Containing Audio Files")
            if not folder or not os.path.exists(folder):
                print("❌ Folder not selected or does not exist.")
                return None, None

            df = pd.read_excel(excel_path)
            if "Audio File" not in df.columns:
                print("❌ Excel must contain 'Audio File' column.")
                return None, None

            files = df["Audio File"].dropna().tolist()
            full_paths = [os.path.join(folder, f) for f in files if os.path.exists(os.path.join(folder, f))]

            if not full_paths:
                print("❌ No valid files found in folder matching Excel list.")
                return None, None

            print(f"✅ Found {len(full_paths)} valid files from Excel to process.")
            return excel_path, full_paths

        except Exception as e:
            print(f"❌ Error reading from Excel: {e}")
            return None, None


        
    # Add this method inside the BatchProcessor class
    def push_folder_to_device(self, local_folder):
        """
        Pushes the selected folder's audio files to the connected Android device.
        Returns the absolute device folder path if successful, None otherwise.
        """
        print(f"📤 Pushing folder to device...")

        try:
            # Remove previous folder on device if exists
            subprocess.run(["adb", "shell", f"rm -rf {device_audio_dir}"], capture_output=True)

            # Create fresh folder
            subprocess.run(["adb", "shell", f"mkdir -p {device_audio_dir}"], capture_output=True)

            # Push all WAV files
            for file in os.listdir(local_folder):
                if file.lower().endswith((".wav", ".mp3", ".flac")):
                    full_path = os.path.join(local_folder, file)
                    subprocess.run(["adb", "push", full_path, device_audio_dir], capture_output=True)

            print(f"✅ Pushed to: {device_audio_dir}")
            return device_audio_dir

        except Exception as e:
            print(f"❌ Failed to push folder: {e}")
            return None

    def add_result(self, audio_file, odg_score, quality_rating, processing_time,
                   interruptions_count, graph_path, success=True, error_message=None):
        self.results.append({
            'Audio File': os.path.basename(audio_file),
            'Full Path': audio_file,
            'ODG Score': odg_score if success else 'N/A',
            'Quality Rating': quality_rating if success else 'Failed',
            'Processing Time (s)': processing_time,
            'Interruptions Count': interruptions_count if success else 'N/A',
            'Graph Path': graph_path if success else 'N/A',
            'Success': success,
            'Error Message': error_message if not success else '',
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    def save_results_to_excel(self):
        if not self.results:
            print("❌ No results to save.")
            return

        try:
            df = pd.DataFrame(self.results)
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Batch Results', index=False)

                summary_data = {
                    'Metric': [
                        'Total Files Processed',
                        'Successful Processes',
                        'Failed Processes',
                        'Average ODG Score',
                        'Best ODG Score',
                        'Worst ODG Score',
                        'Total Processing Time (min)',
                        'Average Processing Time (s)'
                    ],
                    'Value': [
                        len(self.results),
                        sum(r['Success'] for r in self.results),
                        sum(not r['Success'] for r in self.results),
                        np.mean([r['ODG Score'] for r in self.results if isinstance(r['ODG Score'], (int, float))]),
                        max([r['ODG Score'] for r in self.results if isinstance(r['ODG Score'], (int, float))], default='N/A'),
                        min([r['ODG Score'] for r in self.results if isinstance(r['ODG Score'], (int, float))], default='N/A'),
                        sum(r['Processing Time (s)'] for r in self.results) / 60,
                        np.mean([r['Processing Time (s)'] for r in self.results])
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        except Exception as e:
            print(f"❌ Excel export failed: {e}")

    def print_batch_summary(self):
        successful = [r for r in self.results if r['Success']]
        failed = [r for r in self.results if not r['Success']]
        print(f"\n📈 Processed: {len(self.results)} | ✅ Success: {len(successful)} | ❌ Failed: {len(failed)}")
        if successful:
            odg_scores = [r['ODG Score'] for r in successful if isinstance(r['ODG Score'], (float, int))]
            print(f"🏆 Avg ODG: {np.mean(odg_scores):.2f}, Max: {max(odg_scores):.2f}, Min: {min(odg_scores):.2f}")
