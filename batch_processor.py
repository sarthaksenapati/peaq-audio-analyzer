import os
import subprocess
import datetime
from tkinter import filedialog
from openpyxl import Workbook
from openpyxl.styles import Font

class BatchProcessor:
    SUPPORTED_EXTENSIONS = ['.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg', '.opus', '.wma', '.webm', '.mid', '.mp4']

    def __init__(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.batch_root = os.path.join("results/batch_results", f"batch_{timestamp}")
        self.graphs_folder = os.path.join(self.batch_root, "graphs")
        os.makedirs(self.graphs_folder, exist_ok=True)

        self.excel_path = os.path.join(self.batch_root, "batch_results.xlsx")
        self.results = []

    def add_result(self, filename, odg, quality, duration, interruptions=None, graph_path=None, success=True, error_message=None):
        self.results.append({
            "filename": filename,
            "odg": odg,
            "quality": quality,
            "duration": duration,
            "interruptions": interruptions,
            "graph_path": graph_path,
            "success": success,
            "error": error_message
        })

    def print_batch_summary(self):
        print("\n📊 Batch Summary:")
        for r in self.results:
            status = "✅" if r["success"] else "❌"
            print(f"{status} {os.path.basename(r['filename'])}")
            if not r["success"]:
                print(f"   ↳ Error: {r['error']}")

    def save_results_to_excel(self):
        wb = Workbook()
        ws = wb.active
        ws.title = "Results"

        headers = ["Filename", "ODG", "Quality", "Duration (s)", "Interruptions", "Graph Path", "Success", "Error"]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        for r in self.results:
            ws.append([
                os.path.basename(r["filename"]),
                r["odg"],
                r["quality"],
                round(r["duration"], 2) if r["duration"] else None,
                r["interruptions"],
                r["graph_path"],
                "Yes" if r["success"] else "No",
                r["error"]
            ])

        wb.save(self.excel_path)
        print(f"📁 Results saved to {self.excel_path}")

    def select_folder_to_push(self):
        print("📂 Select folder containing audio files to push")
        folder = filedialog.askdirectory()
        if not folder:
            print("❌ No folder selected.")
            return None, []

        if not os.path.isdir(folder):
            print(f"❌ Invalid folder path: {folder}")
            return None, []

        files = os.listdir(folder)
        audio_files = [f for f in files if any(f.lower().endswith(ext) for ext in self.SUPPORTED_EXTENSIONS)]

        if not audio_files:
            print("❌ No supported audio files found in the folder.")
            return None, []

        unsupported = [f for f in files if not any(f.lower().endswith(ext) for ext in self.SUPPORTED_EXTENSIONS)]
        if unsupported:
            print(f"ℹ️ Skipped {len(unsupported)} unsupported files:")
            print("   " + ", ".join(unsupported[:5]) + ("..." if len(unsupported) > 5 else ""))

        return folder, [os.path.join(folder, f) for f in audio_files]

    def push_folder_to_device(self, local_folder, target_path="/sdcard/O6/"):
        if not os.path.isdir(local_folder):
            print(f"❌ Invalid local folder: {local_folder}")
            return None

        print(f"📤 Pushing folder to device: {local_folder} → {target_path}")
        try:
            subprocess.run(["adb", "shell", f"mkdir -p \"{target_path}\""], check=True)
            subprocess.run(["adb", "push", local_folder, target_path], check=True)
            print("✅ Folder pushed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ ADB push failed: {e}")
            return None
