import os
from peaq_analyzer import run_peaq_analysis

def run_peaq_comparison(ref_path, test_path, graph_output_folder):
    os.makedirs(graph_output_folder, exist_ok=True)

    odg, quality = run_peaq_analysis(ref_path, test_path, graph_output_folder=graph_output_folder)

    base_name = os.path.splitext(os.path.basename(ref_path))[0]
    graph_path = os.path.join(graph_output_folder, f"{base_name}.png")

    return {
        "odg": odg,
        "quality": quality,
        "graph_path": graph_path
    }