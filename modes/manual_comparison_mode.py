# modes/manual_comparison_mode.py

import os
from tkinter import Tk, filedialog
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis

def run_manual_comparison_mode():
    print("🎧 Manual Comparison Mode")

    # Set up hidden Tkinter root window for file dialog
    root = Tk()
    root.withdraw()  # Hide the main window

    # Prompt user to select reference and test audio files
    print("\n📂 Select the REFERENCE audio file:")
    ref = filedialog.askopenfilename(
        title="Select Reference File",
        filetypes=[("Audio files", "*.wav *.mp3 *.flac *.m4a *.aac *.ogg *.opus *.wma")]
    )

    if not ref:
        print("❌ Reference file selection cancelled.")
        return

    print("\n📂 Select the TEST audio file:")
    test = filedialog.askopenfilename(
        title="Select Test File",
        filetypes=[("Audio files", "*.wav *.mp3 *.flac *.m4a *.aac *.ogg *.opus *.wma")]
    )

    if not test:
        print("❌ Test file selection cancelled.")
        return

    if ref == test:
        print("❌ Reference and Test files must be different.")
        return

    try:
        ref_dur = get_audio_duration(ref)
        test_dur = get_audio_duration(test)
        print(f"\n✅ Reference: {os.path.basename(ref)} ({ref_dur:.2f}s)")
        print(f"✅ Test     : {os.path.basename(test)} ({test_dur:.2f}s)")
    except Exception as e:
        print(f"⚠️ Error reading durations: {e}")
        return

    graph_output_folder = "results/manual"
    os.makedirs(graph_output_folder, exist_ok=True)

    odg, quality = run_peaq_analysis(ref, test, graph_output_folder)

    if odg is not None:
        print(f"\n🎯 ODG: {odg:.2f} | Quality: {quality}")
