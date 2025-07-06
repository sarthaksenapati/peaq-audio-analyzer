import numpy as np
import matplotlib.pyplot as plt
from PEAQ import PEAQ
from audio_utils import load_audio, align_signals
from utils.plotting_utils import plot_peaq_results
import os


def run_peaq_analysis(ref_path, test_path, graph_output_folder):
    try:
        # Load and align audio
        ref_sr, ref = load_audio(ref_path, target_sr=44100, mono=True)
        test_sr, test = load_audio(test_path, target_sr=44100, mono=True)
        
        print(f"📐 Original signal lengths — ref: {len(ref)}, test: {len(test)}")
        
        ref, test, _ = align_signals(ref, test)

        print(f"📐 Aligned signal lengths — ref: {len(ref)}, test: {len(test)}")
        
        # Enhanced validation
        if ref.size == 0 or test.size == 0:
            raise ValueError("Aligned signals are empty — likely no overlap after trimming.")
        
        if len(ref) < 1024 or len(test) < 1024:
            raise ValueError(f"Signals too short for PEAQ analysis (ref: {len(ref)}, test: {len(test)})")

        # Run PEAQ
        model = PEAQ(fs=44100)
        model.process(ref, test)
        
        # Check if PEAQ processing created valid data
        if not hasattr(model, 'BWRef') or len(model.BWRef) == 0:
            raise ValueError("PEAQ processing failed - no bandwidth data generated")
        
        odg, movs = model.computeODG()
        
        # Validate ODG
        if odg is None or np.isnan(odg) or np.isinf(odg):
            raise ValueError("PEAQ analysis produced invalid ODG value")

        base_name = os.path.splitext(os.path.basename(ref_path))[0]
        graph_path = os.path.join(graph_output_folder, f"{base_name}.png")

        # Use the proper plotting function from plotting_utils
        plot_peaq_results(model, output_path=graph_path, show=False)

        # Quality classification
        quality = (
            "Excellent" if odg > -0.5 else
            "Good" if odg > -1.5 else
            "Satisfactory" if odg > -2.5 else
            "Poor"
        )
        
        print(f"✅ PEAQ Analysis Complete: ODG = {odg:.3f}, Quality = {quality}")
        return odg, quality

    except Exception as e:
        print(f"❌ PEAQ Analysis Failed for {ref_path}: {e}")
        return None, None


def classify_quality(odg):
    if odg >= -0.5:
        return "Excellent"
    elif odg >= -1.5:
        return "Good"
    elif odg >= -2.5:
        return "Satisfactory"
    elif odg >= -3.0:
        return "Poor"
    else:
        return "Bad"