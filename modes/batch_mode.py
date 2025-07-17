import time
import os
from adb_controller import check_adb_connection, push_audio, list_recordings, pull_recording
from flawless_recorder import FlawlessRecorder, get_recorder
from aux_recorder import AuxRecorder
from peaq_analyzer import run_peaq_analysis
from batch_processor import BatchProcessor
from audio_utils import get_audio_duration
from file_manager import select_audio_files
from playback_options import choose_playback_method


def wait_for_new_recording(before_files, max_retries=3, retry_delay=2):
    for attempt in range(max_retries):
        time.sleep(retry_delay)
        after_files = list_recordings()
        new_files = sorted(set(after_files) - set(before_files))
        if new_files:
            print(f"✅ Found {len(new_files)} new recording(s) after {attempt + 1} attempt(s)")
            return new_files
        print(f"⏳ Attempt {attempt + 1}/{max_retries}: No new recordings found, retrying...")
    return []


def process_single_file(file_path, recorder, processor, playback_func):
    print(f"\n🎵 Processing: {os.path.basename(file_path)}")
    start_time = time.time()

    try:
        duration = get_audio_duration(file_path)
        if duration is None or duration <= 0:
            raise ValueError(f"Invalid audio duration: {duration}")

        print(f"📊 Audio duration: {duration:.2f}s")
        print("📤 Pushing audio to device...")
        push_audio(file_path)

        is_az = isinstance(recorder, FlawlessRecorder)
        if is_az:
            before_files = list_recordings()

        print("🎙️ Starting recording with Files app sync...")
        recorder.start(file_path, lambda f: playback_func(f, on_kill_callback=recorder.stop))

        if is_az:
            print("💾 Waiting for recording to be saved...")
            new_files = wait_for_new_recording(before_files)
            if not new_files:
                raise Exception("No new recording found after multiple attempts")
            latest_recording = new_files[-1]
            print(f"📁 Latest recording: {latest_recording}")
            print("📥 Pulling recording from device...")
            pulled_file = pull_recording(latest_recording)

            if not pulled_file or not os.path.exists(pulled_file):
                raise Exception(f"Failed to pull recording: {pulled_file}")
        else:
            print("⏳ Waiting for AUX recording to complete...")
            recorder.stop()
            pulled_file = None  # Not needed for AUX

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        os.makedirs("extracted_audio", exist_ok=True)
        output_clean = os.path.join("extracted_audio", f"{base_name}_clean.wav")

        # ✅ Handle duplicate filename if exists
        if os.path.exists(output_clean):
            os.remove(output_clean)

        print("🔧 Post-processing recording...")
        if not recorder.post_process(pulled_file, file_path, output_clean):
            raise Exception("Post-processing failed")

        if not os.path.exists(output_clean):
            raise Exception(f"Post-processed file not created: {output_clean}")

        print("📈 Running PEAQ analysis...")
        odg, quality = run_peaq_analysis(file_path, output_clean, processor.graphs_folder)
        if odg is None or quality is None:
            raise Exception("PEAQ analysis failed")

        graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")
        interruptions_count = len(getattr(recorder.tracker, 'interruptions', []))

        processor.add_result(
            file_path, odg, quality,
            time.time() - start_time,
            interruptions_count,
            graph_path=graph_path,
            success=True
        )

        print(f"✅ Successfully processed: ODG={odg:.2f}, Quality={quality}")
        return True

    except Exception as e:
        print(f"❌ Error processing {os.path.basename(file_path)}: {str(e)}")
        processor.add_result(
            file_path, None, None,
            time.time() - start_time,
            None, None,
            success=False,
            error_message=str(e)
        )
        return False


def run_batch_mode():
    print("📦 Starting Batch Mode")
    print("=" * 50)

    if not check_adb_connection():
        print("❌ No ADB device connected.")
        return

    print("✅ ADB connection verified")
    audio_files = select_audio_files()
    if not audio_files:
        print("❌ No audio files selected.")
        return

    print(f"📁 Selected {len(audio_files)} audio file(s)")

    # 📌 Ask user for recording method
    print("\n🎙️ Select recording method:")
    print("  [1] AZ Screen Recorder (Phone)")
    print("  [2] AUX Cable Recording (PC)")
    recorder_choice = input("> ").strip()

    if recorder_choice == '2':
        recorder = AuxRecorder()
        if not recorder.prompt_and_set_device():
            print("❌ Aborting: No valid AUX device selected.")
            return
    else:
        recorder = FlawlessRecorder()

    processor = BatchProcessor()
    os.makedirs("extracted_audio", exist_ok=True)
    os.makedirs(processor.graphs_folder, exist_ok=True)

    playback_func = choose_playback_method()
    successful_count = 0
    total_start_time = time.time()

    for i, file_path in enumerate(audio_files, 1):
        print(f"\n{'=' * 20} File {i}/{len(audio_files)} {'=' * 20}")
        if process_single_file(file_path, recorder, processor, playback_func):
            successful_count += 1
        if i < len(audio_files):
            print("⏳ Waiting before next file...")
            time.sleep(1)

    total_time = time.time() - total_start_time
    print(f"\n{'=' * 50}")
    print("📊 BATCH PROCESSING COMPLETE")
    print(f"Total files: {len(audio_files)}")
    print(f"Successful: {successful_count}")
    print(f"Failed: {len(audio_files) - successful_count}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per file: {total_time / len(audio_files):.1f}s")

    try:
        processor.save_results_to_excel()
        print("✅ Results saved to Excel")
    except Exception as e:
        print(f"❌ Failed to save Excel results: {e}")

    processor.print_batch_summary()


if __name__ == "__main__":
    run_batch_mode()
