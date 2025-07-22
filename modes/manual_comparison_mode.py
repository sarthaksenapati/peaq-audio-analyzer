# modes/manual_comparison_mode.py

import glob
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis
import os

def run_manual_comparison_mode():
    print("Manual Comparison Mode")

    # ✅ List of common formats — can add more as needed
    all_files = []
    extensions = ['*.wav', '*.mp3', '*.flac', '*.m4a', '*.aac', '*.ogg', '*.opus', '*.wma']
    for ext in extensions:
        all_files.extend(glob.glob(ext))
        all_files.extend(glob.glob(ext.upper()))

    if len(all_files) < 2:
        print("Need at least 2 audio files.")
        return

    for i, f in enumerate(all_files, 1):
        try:
            dur = get_audio_duration(f)
            print(f"  [{i}] {f} ({dur:.2f}s)")
        except:
            print(f"  [{i}] {f} (unknown or unreadable)")

    def pick(msg):
        while True:
            try:
                i = int(input(msg)) - 1
                if 0 <= i < len(all_files): return all_files[i]
                print("Try again.")
            except:
                print("Invalid input.")

    ref = pick("\nSelect REFERENCE file number: ")
    test = pick("Select TEST file number: ")
    if ref == test:
        print("Files must be different.")
        return

    graph_output_folder = "manual"
    os.makedirs(graph_output_folder, exist_ok=True)

    odg, quality = run_peaq_analysis(ref, test, graph_output_folder)

    if odg is not None:
        print(f"\n🎯 ODG: {odg:.2f} | Quality: {quality}")
