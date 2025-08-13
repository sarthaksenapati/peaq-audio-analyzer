## peaq_analyzer.py
import os
import numpy as np
from PEAQ import PEAQ
from audio_utils import load_audio, align_signals_by_cross_correlation
from utils.plotting_utils import plot_peaq_results
import config


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

        # Apply sample-level delay compensation BEFORE any other processing
        if (hasattr(config, 'ENABLE_AUTO_DELAY_COMPENSATION') and 
            config.ENABLE_AUTO_DELAY_COMPENSATION and
            hasattr(config, 'SAMPLE_DELAY_COMPENSATION')):
            
            delay_samples = config.SAMPLE_DELAY_COMPENSATION
            print(f"🔧 Applying {delay_samples} sample delay compensation ({delay_samples/ref_sr*1000:.1f}ms)")
            
            # Trim the delay from the test signal
            if len(test) > delay_samples:
                test = test[delay_samples:]
                print(f"✂️ Test signal trimmed by {delay_samples} samples")
            else:
                print("⚠️ Test signal too short for delay compensation")

        # Ensure both signals are the same length after delay compensation
        min_len = min(len(ref), len(test))
        ref = ref[:min_len]
        test = test[:min_len]
        
        print(f"📐 Final aligned lengths — ref: {len(ref)}, test: {len(test)}")

        # Calculate signal difference after sample-level alignment
        diff_after = np.mean(np.abs(ref - test))
        print(f"🔍 Signal difference after sample-level alignment: {diff_after:.6f}")

        # Skip cross-correlation alignment since we've done sample-level alignment
        print("🚫 Skipping cross-correlation alignment (using sample-level compensation)")

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
    if odg >= -1.0:
        return "Excellent"
    elif odg >= -2.0:
        return "Good"
    elif odg >= -3.0:
        return "Fair"
    elif odg >= -4.0:
        return "Poor"
    else:
        return "Bad"
