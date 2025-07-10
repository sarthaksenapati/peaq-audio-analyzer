## peaq_analyzer.py
import os
import numpy as np
from PEAQ import PEAQ
from audio_utils import load_audio, align_signals_by_cross_correlation
from utils.plotting_utils import plot_peaq_results


def run_peaq_analysis(ref_path, test_path, graph_output_folder):
    try:
        print("\n" + "=" * 60)
        print("🔬 STARTING PEAQ AUDIO QUALITY ANALYSIS")
        print("=" * 60)

        ref_sr, ref = load_audio(ref_path)
        test_sr, test = load_audio(test_path)

        print(f"📁 Reference: {ref_path}")
        print(f"📁 Test: {test_path}")
        print(f"📐 Original lengths — ref: {len(ref)}, test: {len(test)}")

        min_len_before = min(len(ref), len(test))
        diff_before = np.mean(np.abs(ref[:min_len_before] - test[:min_len_before]))
        print(f"🔍 Signal difference BEFORE alignment: {diff_before:.6f}")

        # ✅ Use your proven waveform-level cross-correlation
        ref, test, lag = align_signals_by_cross_correlation(ref, test)

        diff_after = np.mean(np.abs(ref - test))
        print(f"🧭 Aligned signals by shifting by {lag / ref_sr:.3f} seconds")
        print(f"📐 Aligned lengths — ref: {len(ref)}, test: {len(test)}")
        print(f"🔍 Signal difference AFTER alignment: {diff_after:.6f}")

        if len(ref) < 1024 or len(test) < 1024:
            raise ValueError("Signals too short for PEAQ analysis")

        model = PEAQ(fs=ref_sr)
        model.process(ref, test)

        if not hasattr(model, 'BWRef') or len(model.BWRef) == 0:
            raise ValueError("PEAQ model did not produce bandwidth output")

        odg, movs = model.computeODG()

        if odg is None or np.isnan(odg) or np.isinf(odg):
            raise ValueError("ODG value is invalid")

        base_name = os.path.splitext(os.path.basename(ref_path))[0]
        graph_path = os.path.join(graph_output_folder, f"{base_name}.png")
        plot_peaq_results(model, output_path=graph_path, show=False)

        quality = classify_quality(odg)

        print(f"✅ ODG = {odg:.2f} | Quality = {quality}")
        print(f"📊 Plot saved to: {graph_path}")
        return odg, quality

    except Exception as e:
        print(f"❌ PEAQ Analysis Failed: {e}")
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
