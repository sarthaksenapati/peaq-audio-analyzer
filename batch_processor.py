## batch_processor.py

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
        """Create timestamped batch folders for results and graphs"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.batch_folder = os.path.join(batch_results_dir, f"batch_{timestamp}")
            self.graphs_folder = os.path.join(self.batch_folder, "graphs")
            
            # Create directories with proper error handling
            os.makedirs(self.batch_folder, exist_ok=True)
            os.makedirs(self.graphs_folder, exist_ok=True)
            
            self.excel_file = os.path.join(self.batch_folder, "batch_results.xlsx")
            
            print(f"📁 Batch folder created: {self.batch_folder}")
            print(f"📊 Graphs folder: {self.graphs_folder}")
            
        except Exception as e:
            print(f"❌ Failed to create batch folders: {e}")
            # Fallback to current directory
            self.batch_folder = f"batch_{timestamp}"
            self.graphs_folder = os.path.join(self.batch_folder, "graphs")
            os.makedirs(self.batch_folder, exist_ok=True)
            os.makedirs(self.graphs_folder, exist_ok=True)
            self.excel_file = os.path.join(self.batch_folder, "batch_results.xlsx")

    def select_folder_to_push(self):
        """Use a GUI dialog to select a folder containing audio files."""
        try:
            # Initialize tkinter properly
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.lift()  # Bring to front
            root.attributes('-topmost', True)  # Keep on top
            
            folder = filedialog.askdirectory(
                title="Select Folder for Batch Push",
                parent=root
            )
            
            root.destroy()  # Clean up tkinter
            
            if not folder:
                print("❌ No folder selected.")
                return None
                
            if not os.path.exists(folder):
                print(f"❌ Selected folder does not exist: {folder}")
                return None
                
            # Look for audio files with multiple extensions
            audio_extensions = ['.wav', '.mp3', '.flac', '.m4a', '.aac']
            audio_files = []
            
            for file in os.listdir(folder):
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    audio_files.append(file)
            
            if not audio_files:
                print(f"⚠️  Selected folder does not contain any audio files.")
                print(f"   Looking for: {', '.join(audio_extensions)}")
                return None
            
            full_paths = [os.path.join(folder, f) for f in audio_files]
            print(f"📁 Selected folder: {folder}")
            print(f"🎵 Found {len(audio_files)} audio files")
            
            return folder, full_paths
            
        except Exception as e:
            print(f"❌ Error selecting folder: {e}")
            return None    

    def read_files_from_excel(self):
        """
        Asks user to select an Excel file and a folder.
        Returns: (excel_path, list of full audio paths to process)
        """
        try:
            root = tk.Tk()
            root.withdraw()
            root.lift()
            root.attributes('-topmost', True)
            
            # Select Excel file
            excel_path = filedialog.askopenfilename(
                title="Select Excel File with Audio Filenames",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
                parent=root
            )
            
            if not excel_path:
                print("❌ No Excel file selected.")
                root.destroy()
                return None, None
                
            if not os.path.exists(excel_path):
                print(f"❌ Excel file does not exist: {excel_path}")
                root.destroy()
                return None, None

            # Select folder containing audio files
            folder = filedialog.askdirectory(
                title="Select Folder Containing Audio Files",
                parent=root
            )
            
            root.destroy()
            
            if not folder:
                print("❌ No folder selected.")
                return None, None
                
            if not os.path.exists(folder):
                print(f"❌ Folder does not exist: {folder}")
                return None, None

            # Read Excel file
            print(f"📖 Reading Excel file: {excel_path}")
            df = pd.read_excel(excel_path)
            
            # Check for required column
            if "Audio File" not in df.columns:
                print("❌ Excel must contain 'Audio File' column.")
                print(f"   Available columns: {list(df.columns)}")
                return None, None

            # Get file list and validate
            files = df["Audio File"].dropna().tolist()
            if not files:
                print("❌ No files found in 'Audio File' column.")
                return None, None

            # Build full paths and check existence
            full_paths = []
            missing_files = []
            
            for file in files:
                full_path = os.path.join(folder, file)
                if os.path.exists(full_path):
                    full_paths.append(full_path)
                else:
                    missing_files.append(file)

            if missing_files:
                print(f"⚠️  {len(missing_files)} files from Excel not found in folder:")
                for file in missing_files[:5]:  # Show first 5 missing files
                    print(f"   - {file}")
                if len(missing_files) > 5:
                    print(f"   ... and {len(missing_files) - 5} more")

            if not full_paths:
                print("❌ No valid files found in folder matching Excel list.")
                return None, None

            print(f"✅ Found {len(full_paths)} valid files from Excel to process.")
            return excel_path, full_paths

        except Exception as e:
            print(f"❌ Error reading from Excel: {e}")
            return None, None

    def push_folder_to_device(self, local_folder):
        """
        Pushes the selected folder's audio files to the connected Android device.
        Returns the absolute device folder path if successful, None otherwise.
        """
        print(f"📤 Pushing folder to device...")

        try:
            # Check if ADB is available
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            if "device" not in result.stdout:
                print("❌ No ADB device connected.")
                return None

            # Remove previous folder on device if exists
            print("🧹 Cleaning previous files on device...")
            subprocess.run(
                ["adb", "shell", f"rm -rf {device_audio_dir}"], 
                capture_output=True, 
                check=False  # Don't fail if folder doesn't exist
            )

            # Create fresh folder
            result = subprocess.run(
                ["adb", "shell", f"mkdir -p {device_audio_dir}"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Failed to create device folder: {result.stderr}")
                return None

            # Get list of audio files to push
            audio_extensions = ['.wav', '.mp3', '.flac', '.m4a', '.aac']
            audio_files = []
            
            for file in os.listdir(local_folder):
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    audio_files.append(file)

            if not audio_files:
                print("❌ No audio files found in folder to push.")
                return None

            # Push all audio files
            pushed_count = 0
            failed_count = 0
            
            print(f"📁 Pushing {len(audio_files)} audio files...")
            
            for file in audio_files:
                full_path = os.path.join(local_folder, file)
                result = subprocess.run(
                    ["adb", "push", full_path, device_audio_dir], 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode == 0:
                    pushed_count += 1
                    print(f"  ✅ {file}")
                else:
                    failed_count += 1
                    print(f"  ❌ {file}: {result.stderr.strip()}")

            print(f"📊 Push complete: {pushed_count} successful, {failed_count} failed")
            
            if pushed_count == 0:
                print("❌ No files were successfully pushed.")
                return None

            print(f"✅ Pushed to: {device_audio_dir}")
            return device_audio_dir

        except FileNotFoundError:
            print("❌ ADB not found. Please install Android SDK platform tools.")
            return None
        except Exception as e:
            print(f"❌ Failed to push folder: {e}")
            return None

    def add_result(self, audio_file, odg_score, quality_rating, processing_time,
                   interruptions_count, graph_path=None, success=True, error_message=None):
        """Add a processing result to the batch results"""
        try:
            result = {
                'Audio File': os.path.basename(audio_file) if audio_file else 'Unknown',
                'Full Path': audio_file if audio_file else 'Unknown',
                'ODG Score': odg_score if success and odg_score is not None else 'N/A',
                'Quality Rating': quality_rating if success and quality_rating else 'Failed',
                'Processing Time (s)': round(processing_time, 2) if processing_time else 0,
                'Interruptions Count': interruptions_count if success and interruptions_count is not None else 'N/A',
                'Graph Path': graph_path if success and graph_path else 'N/A',
                'Success': success,
                'Error Message': error_message if not success else '',
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.results.append(result)
            
            # Log the result
            if success:
                print(f"✅ Added successful result for: {os.path.basename(audio_file)}")
            else:
                print(f"❌ Added failed result for: {os.path.basename(audio_file)} - {error_message}")
                
        except Exception as e:
            print(f"❌ Error adding result: {e}")

    def save_results_to_excel(self):
        """Save batch results to Excel file with comprehensive summary"""
        if not self.results:
            print("❌ No results to save.")
            return

        try:
            df = pd.DataFrame(self.results)
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                # Main results sheet
                df.to_excel(writer, sheet_name='Batch Results', index=False)

                # Calculate summary statistics safely
                successful_results = [r for r in self.results if r['Success']]
                failed_results = [r for r in self.results if not r['Success']]
                
                # Get valid ODG scores
                odg_scores = []
                for r in successful_results:
                    if isinstance(r['ODG Score'], (int, float)) and not np.isnan(r['ODG Score']):
                        odg_scores.append(r['ODG Score'])
                
                # Get valid processing times
                processing_times = []
                for r in self.results:
                    if isinstance(r['Processing Time (s)'], (int, float)) and not np.isnan(r['Processing Time (s)']):
                        processing_times.append(r['Processing Time (s)'])

                # Create summary data
                summary_data = {
                    'Metric': [
                        'Total Files Processed',
                        'Successful Processes',
                        'Failed Processes',
                        'Success Rate (%)',
                        'Average ODG Score',
                        'Best ODG Score',
                        'Worst ODG Score',
                        'Total Processing Time (min)',
                        'Average Processing Time (s)'
                    ],
                    'Value': [
                        len(self.results),
                        len(successful_results),
                        len(failed_results),
                        round((len(successful_results) / len(self.results)) * 100, 1) if self.results else 0,
                        round(np.mean(odg_scores), 3) if odg_scores else 'N/A',
                        round(max(odg_scores), 3) if odg_scores else 'N/A',
                        round(min(odg_scores), 3) if odg_scores else 'N/A',
                        round(sum(processing_times) / 60, 2) if processing_times else 'N/A',
                        round(np.mean(processing_times), 2) if processing_times else 'N/A'
                    ]
                }
                
                # Save summary sheet
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                # Save failed results details if any
                if failed_results:
                    failed_df = pd.DataFrame(failed_results)
                    failed_df.to_excel(writer, sheet_name='Failed Results', index=False)

            print(f"📊 Results saved to: {self.excel_file}")
            
        except Exception as e:
            print(f"❌ Excel export failed: {e}")
            # Try to save as CSV as fallback
            try:
                csv_file = self.excel_file.replace('.xlsx', '.csv')
                df.to_csv(csv_file, index=False)
                print(f"📄 Saved as CSV instead: {csv_file}")
            except Exception as csv_e:
                print(f"❌ CSV export also failed: {csv_e}")

    def print_batch_summary(self):
        """Print a comprehensive batch processing summary"""
        if not self.results:
            print("❌ No results to summarize.")
            return

        try:
            successful = [r for r in self.results if r['Success']]
            failed = [r for r in self.results if not r['Success']]
            
            print(f"\n{'='*50}")
            print("📊 BATCH PROCESSING SUMMARY")
            print(f"{'='*50}")
            print(f"📁 Total files processed: {len(self.results)}")
            print(f"✅ Successful: {len(successful)}")
            print(f"❌ Failed: {len(failed)}")
            
            if self.results:
                success_rate = (len(successful) / len(self.results)) * 100
                print(f"📈 Success rate: {success_rate:.1f}%")
            
            # ODG statistics
            if successful:
                odg_scores = []
                for r in successful:
                    if isinstance(r['ODG Score'], (float, int)) and not np.isnan(r['ODG Score']):
                        odg_scores.append(r['ODG Score'])
                
                if odg_scores:
                    print(f"\n🎯 ODG SCORES:")
                    print(f"   Average: {np.mean(odg_scores):.3f}")
                    print(f"   Best: {max(odg_scores):.3f}")
                    print(f"   Worst: {min(odg_scores):.3f}")
                    print(f"   Std Dev: {np.std(odg_scores):.3f}")
            
            # Processing time statistics
            processing_times = []
            for r in self.results:
                if isinstance(r['Processing Time (s)'], (float, int)) and not np.isnan(r['Processing Time (s)']):
                    processing_times.append(r['Processing Time (s)'])
            
            if processing_times:
                print(f"\n⏱️  PROCESSING TIME:")
                print(f"   Total: {sum(processing_times)/60:.1f} minutes")
                print(f"   Average per file: {np.mean(processing_times):.1f} seconds")
                print(f"   Fastest: {min(processing_times):.1f} seconds")
                print(f"   Slowest: {max(processing_times):.1f} seconds")
            
            # Error summary
            if failed:
                print(f"\n❌ FAILED FILES:")
                error_counts = {}
                for r in failed:
                    error_msg = r.get('Error Message', 'Unknown error')
                    # Get first part of error message for grouping
                    error_key = error_msg.split(':')[0] if ':' in error_msg else error_msg
                    error_counts[error_key] = error_counts.get(error_key, 0) + 1
                
                for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"   {error}: {count} files")
            
            print(f"\n📁 Results saved in: {self.batch_folder}")
            print(f"{'='*50}")
            
        except Exception as e:
            print(f"❌ Error printing summary: {e}")
            # Basic fallback summary
            print(f"\n📈 Basic Summary: {len(self.results)} processed | "
                  f"Success: {sum(1 for r in self.results if r['Success'])} | "
                  f"Failed: {sum(1 for r in self.results if not r['Success'])}")

    def get_batch_folder(self):
        """Get the current batch folder path"""
        return self.batch_folder
    
    def get_graphs_folder(self):
        """Get the graphs folder path"""
        return self.graphs_folder
    
    def clear_results(self):
        """Clear all results (useful for testing)"""
        self.results = []
        print("🧹 Results cleared.")