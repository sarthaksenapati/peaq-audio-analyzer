import time
import os
from adb_controller import check_adb_connection, push_audio, list_recordings, pull_recording
from flawless_recorder import FlawlessRecorder
from peaq_analyzer import run_peaq_analysis
from batch_processor import BatchProcessor
from audio_utils import get_audio_duration
from file_manager import select_audio_files
from playback_options import choose_playback_method  # ✅ New import


def wait_for_new_recording(before_files, max_retries=3, retry_delay=2):
    """Wait for new recording to appear with retries"""
    for attempt in range(max_retries):
        time.sleep(retry_delay)
        after_files = list_recordings()
        new_files = sorted(set(after_files) - set(before_files))
        
        if new_files:
            print(f"✅ Found {len(new_files)} new recording(s) after {attempt + 1} attempt(s)")
            return new_files
        
        print(f"⏳ Attempt {attempt + 1}/{max_retries}: No new recordings found, retrying...")
    
    return []


def process_single_file(file_path, recorder, processor, play_func):
    """Process a single audio file and return success status"""
    print(f"\n🎵 Processing: {os.path.basename(file_path)}")
    start_time = time.time()
    
    try:
        duration = get_audio_duration(file_path)
        if duration is None or duration <= 0:
            raise ValueError(f"Invalid audio duration: {duration}")
        
        print(f"📊 Audio duration: {duration:.2f}s")
        
        print("📤 Pushing audio to device...")
        push_audio(file_path)
        
        before_files = list_recordings()
        print(f"📋 Initial recordings count: {len(before_files)}")
        
        print("🎙️ Starting recording...")
        recorder.start(file_path, play_func)

        wait_time = duration 
        print(f"⏱️ Waiting {wait_time:.1f}s for playback...")
        time.sleep(wait_time)

        print("⏹️ Stopping recording...")
        recorder.stop()
        
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
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_clean = os.path.join("extracted_audio", f"{base_name}_clean.wav")
        os.makedirs("extracted_audio", exist_ok=True)
        
        print("🔧 Post-processing recording...")
        if not recorder.post_process(pulled_file, file_path, output_clean):
            raise Exception("Post-processing failed")
        
        if not os.path.exists(output_clean):
            raise Exception(f"Post-processed file not created: {output_clean}")
        
        print("📈 Running PEAQ analysis...")
        odg, quality = run_peaq_analysis(file_path, output_clean, processor.graphs_folder)
        
        if odg is None or quality is None:
            raise Exception("PEAQ analysis failed - no results returned")
        
        graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")
        interruptions_count = len(getattr(recorder.tracker, 'interruptions', []))
        
        processor.add_result(
            file_path,
            odg,
            quality,
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
            file_path,
            None,
            None,
            time.time() - start_time,
            None,
            None,
            success=False,
            error_message=str(e)
        )
        
        return False


def run_batch_mode():
    print("📦 Starting Batch Mode")
    print("=" * 50)
    
    if not check_adb_connection():
        print("❌ No ADB device connected.")
        print("Please connect your Android device and enable USB debugging.")
        return
    
    print("✅ ADB connection verified")
    
    audio_files = select_audio_files()
    if not audio_files:
        print("❌ No audio files selected.")
        return
    
    print(f"📁 Selected {len(audio_files)} audio file(s)")
    
    recorder = FlawlessRecorder()
    processor = BatchProcessor()
    
    os.makedirs("extracted_audio", exist_ok=True)
    os.makedirs(processor.graphs_folder, exist_ok=True)

    # ✅ Ask user how to play the audio (YT Music vs Files)
    play_func = choose_playback_method()
    
    successful_count = 0
    total_start_time = time.time()
    
    for i, file_path in enumerate(audio_files, 1):
        print(f"\n{'='*20} File {i}/{len(audio_files)} {'='*20}")
        
        if process_single_file(file_path, recorder, processor, play_func):
            successful_count += 1
        
        if i < len(audio_files):
            print("⏳ Waiting before next file...")
            time.sleep(1)
    
    total_time = time.time() - total_start_time
    print(f"\n{'='*50}")
    print("📊 BATCH PROCESSING COMPLETE")
    print(f"Total files: {len(audio_files)}")
    print(f"Successful: {successful_count}")
    print(f"Failed: {len(audio_files) - successful_count}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per file: {total_time/len(audio_files):.1f}s")
    
    try:
        processor.save_results_to_excel()
        print("✅ Results saved to Excel")
    except Exception as e:
        print(f"❌ Failed to save Excel results: {e}")
    
    processor.print_batch_summary()


if __name__ == "__main__":
    run_batch_mode()
