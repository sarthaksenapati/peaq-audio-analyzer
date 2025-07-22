import os
import time
import subprocess
from batch_processor import BatchProcessor
from aux_recorder import AuxRecorder
from adb_controller import check_adb_connection, push_audio
from audio_utils import get_audio_duration
from peaq_analyzer import run_peaq_analysis
from playback_options import choose_playback_method


def run_folder_push_batch_mode():
    print("🌀 Folder Push Batch Mode")

    if not check_adb_connection():
        return

    recorder = AuxRecorder()
    if not recorder.prompt_and_set_device():
        print("❌ Aborting: No valid AUX device selected.")
        return

    processor = BatchProcessor()
    folder_result = processor.select_folder_to_push()
    if not folder_result:
        print("❌ No folder selected.")
        return

    local_folder, audio_files = folder_result
    print(f"📁 Selected folder: {local_folder} with {len(audio_files)} audio files.")

    if not audio_files:
        print("❌ No audio files found in the selected folder.")
        return

    playback_func = choose_playback_method()

    for audio_file in audio_files:
        start_time = time.time()
        base_name = os.path.splitext(os.path.basename(audio_file))[0]

        try:
            # 🔁 Convert to WAV if needed
            if not audio_file.lower().endswith(".wav"):
                converted_path = os.path.join("temp_converted", f"{base_name}.wav")
                os.makedirs("temp_converted", exist_ok=True)
                subprocess.run([
                    "ffmpeg", "-y", "-i", audio_file,
                    "-ar", "44100", "-ac", "2", converted_path
                ], capture_output=True)
                audio_input = converted_path
            else:
                audio_input = audio_file

            duration = get_audio_duration(audio_input)

            push_audio(audio_input)

            print("🎙️ Starting recording with Files app sync...")
            recorder.start(audio_input, lambda f: playback_func(f, on_kill_callback=recorder.stop))

            print("⏳ Waiting for AUX recording to complete...")
            recorder.stop()

            output_clean = os.path.join("extracted_audio", f"{base_name}_clean.wav")
            os.makedirs("extracted_audio", exist_ok=True)

            if os.path.exists(output_clean):
                os.remove(output_clean)

            if not recorder.post_process(None, audio_input, output_clean):
                raise RuntimeError("Post-processing failed.")

            odg, quality = run_peaq_analysis(audio_input, output_clean, processor.graphs_folder)
            if odg is None:
                raise RuntimeError("PEAQ analysis failed.")

            graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")
            interruptions = len(getattr(recorder.tracker, 'interruptions', []))

            processor.add_result(
                audio_file, odg, quality,
                time.time() - start_time,
                interruptions,
                graph_path
            )
            processor.save_results_to_excel()

        except Exception as e:
            processor.add_result(audio_file, None, None, time.time() - start_time,
                                 None, None, success=False, error_message=str(e))

    processor.save_results_to_excel()
    processor.print_batch_summary()
