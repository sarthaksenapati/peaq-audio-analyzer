import os
import traceback
from batch_processor import BatchProcessor
from wrapper_peaq import run_peaq_comparison
from audio_utils import get_audio_duration

def run_spotify_comparison_mode():
    print("📊 Spotify Comparison Mode – Folder Matching")

    ref_folder = "phone1_tracks"
    test_folder = "phone2_tracks"

    if not os.path.isdir(ref_folder) or not os.path.isdir(test_folder):
        print("❌ Missing reference or test folders.")
        return

    processor = BatchProcessor()

    all_files = sorted(os.listdir(ref_folder))
    for fname in all_files:
        ref_path = os.path.join(ref_folder, fname)
        test_path = os.path.join(test_folder, fname)

        if not os.path.isfile(test_path):
            print(f"⚠️ Skipping {fname} — test file not found")
            continue

        try:
            print(f"\n============================================================")
            print(f"🔬 STARTING PEAQ AUDIO QUALITY ANALYSIS")
            print(f"📁 Reference: {ref_path}")
            print(f"📁 Test: {test_path}")

            # ✅ Expecting a dict return from run_peaq_comparison()
            result = run_peaq_comparison(ref_path, test_path, processor.graphs_folder)

            odg = result.get("odg")
            quality = result.get("quality")
            graph_path = result.get("graph_path", None)

            duration = get_audio_duration(ref_path)

            if odg is not None and quality is not None:
                print(f"✅ Compared {fname}: ODG = {odg:.3f}, Quality = {quality}")
            else:
                print(f"⚠️ Compared {fname}: ODG/Quality not available (analysis failed)")

            processor.add_result(
                filename=fname,
                odg=odg,
                quality=quality,
                duration=duration,
                graph_path=graph_path,
            )

        except Exception as e:
            print(f"❌ Error comparing {fname}: {str(e)}")
            traceback.print_exc()
            processor.add_result(
                filename=fname,
                odg=None,
                quality=None,
                duration=None,
                graph_path=None,
                success=False,
                error_message=str(e)
            )

    processor.print_batch_summary()
    processor.save_results_to_excel()

if __name__ == "__main__":
    run_spotify_comparison_mode()