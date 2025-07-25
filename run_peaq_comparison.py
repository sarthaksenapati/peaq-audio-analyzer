import os
import pandas as pd
from wrapper_peaq import run_peaq_comparison

def compare_folders(phone1_folder, phone2_folder, output_xlsx_path, graph_folder):
    os.makedirs(graph_folder, exist_ok=True)
    results = []

    phone1_files = sorted(os.listdir(phone1_folder))
    phone2_files = sorted(os.listdir(phone2_folder))

    for f1, f2 in zip(phone1_files, phone2_files):
        path1 = os.path.join(phone1_folder, f1)
        path2 = os.path.join(phone2_folder, f2)

        odg_dict = run_peaq_comparison(path1, path2)

        results.append({
            "Track": f1,
            "ODG": odg_dict.get("ODG", None)
        })

    df = pd.DataFrame(results)
    df.to_excel(output_xlsx_path, index=False)
    print(f"📊 ODG results saved to: {output_xlsx_path}")
