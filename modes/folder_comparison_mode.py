# modes/folder_comparison_mode.py

import os
import glob
import pandas as pd
from peaq_analyzer import run_peaq_analysis

def run_folder_comparison_mode():
    print("📂 Folder Comparison Mode — Batch PEAQ Evaluation\n")

    folder1 = input("Enter path to phone1 folder (reference): ").strip('"')
    folder2 = input("Enter path to phone2 folder (test): ").strip('"')

    if not os.path.isdir(folder1) or not os.path.isdir(folder2):
        print("❌ One or both folders do not exist.")
        return

    files1 = sorted([f for f in os.listdir(folder1) if f.lower().endswith(('.wav', '.mp3', '.flac', '.m4a'))])
    files2 = sorted([f for f in os.listdir(folder2) if f.lower().endswith(('.wav', '.mp3', '.flac', '.m4a'))])

    common_files = sorted(set(files1) & set(files2))

    if not common_files:
        print("❌ No matching audio filenames found in both folders.")
        return

    print(f"🔍 Found {len(common_files)} matching files:\n" + "\n".join(f"  - {f}" for f in common_files))

    results = []
    output_dir = "folder_comparison_results"
    os.makedirs(output_dir, exist_ok=True)
    graph_dir = os.path.join(output_dir, "graphs")
    os.makedirs(graph_dir, exist_ok=True)

    for file in common_files:
        ref_path = os.path.join(folder1, file)
        test_path = os.path.join(folder2, file)

        print(f"\n🔬 Comparing: {file}")
        odg, quality = run_peaq_analysis(ref_path, test_path, graph_output_folder=graph_dir)

        results.append({
            "Filename": file,
            "ODG": odg,
            "Quality": quality
        })

    # Save results to Excel
    df = pd.DataFrame(results)
    excel_path = os.path.join(output_dir, "comparison_results.xlsx")
    df.to_excel(excel_path, index=False)
    print(f"\n✅ Comparison complete! Results saved to: {excel_path}")
    print(f"📊 Graphs saved in: {graph_dir}")
