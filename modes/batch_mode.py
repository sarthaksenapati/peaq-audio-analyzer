import time
import os
from adb_controller import check_adb_connection, push_audio, list_recordings, pull_recording
from flawless_recorder import FlawlessRecorder
from peaq_analyzer import run_peaq_analysis
from batch_processor import BatchProcessor
from audio_utils import get_audio_duration
from file_manager import select_audio_files


def play_audio(file_path):
    """Play audio file on Android device"""
    filename = os.path.basename(file_path)
    device_path = f"/sdcard/{filename}"
    os.system(f'adb shell am start -a android.intent.action.VIEW -d file://{device_path} -t audio/wav')


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


def process_single_file(file_path, recorder, processor):
    """Process a single audio file and return success status"""
    print(f"\n🎵 Processing: {os.path.basename(file_path)}")
    start_time = time.time()
    
    try:
        # Get audio duration
        duration = get_audio_duration(file_path)
        if duration is None or duration <= 0:
            raise ValueError(f"Invalid audio duration: {duration}")
        
        print(f"📊 Audio duration: {duration:.2f}s")
        
        # Push audio to device
        print("📤 Pushing audio to device...")
        push_audio(file_path)
        
        # Get initial recording list
        before_files = list_recordings()
        print(f"📋 Initial recordings count: {len(before_files)}")
        
        # Start recording
        print("🎙️ Starting recording...")
        recorder.start(file_path, play_audio)
        
        # Wait for audio to play + buffer
        wait_time = duration + 2
        print(f"⏱️ Waiting {wait_time:.1f}s for playback...")
        time.sleep(wait_time)
        
        # Stop recording
        print("⏹️ Stopping recording...")
        recorder.stop()
        
        # Wait for recording to be saved
        print("💾 Waiting for recording to be saved...")
        new_files = wait_for_new_recording(before_files)
        
        if not new_files:
            raise Exception("No new recording found after multiple attempts")
        
        # Get the latest recording
        latest_recording = new_files[-1]
        print(f"📁 Latest recording: {latest_recording}")
        
        # Pull recording from device
        print("📥 Pulling recording from device...")
        pulled_file = pull_recording(latest_recording)
        
        if not pulled_file or not os.path.exists(pulled_file):
            raise Exception(f"Failed to pull recording: {pulled_file}")
        
        # Prepare output path
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_clean = os.path.join("extracted_audio", f"{base_name}_clean.wav")
        
        # Ensure output directory exists
        os.makedirs("extracted_audio", exist_ok=True)
        
        # Post-process the recording
        print("🔧 Post-processing recording...")
        if not recorder.post_process(pulled_file, file_path, output_clean):
            raise Exception("Post-processing failed")
        
        if not os.path.exists(output_clean):
            raise Exception(f"Post-processed file not created: {output_clean}")
        
        # Run PEAQ analysis
        print("📈 Running PEAQ analysis...")
        odg, quality = run_peaq_analysis(file_path, output_clean, processor.graphs_folder)
        
        if odg is None or quality is None:
            raise Exception("PEAQ analysis failed - no results returned")
        
        # Prepare graph path
        graph_path = os.path.join(processor.graphs_folder, f"{base_name}.png")
        
        # Get interruptions count safely
        interruptions_count = 0
        if hasattr(recorder, 'tracker') and hasattr(recorder.tracker, 'interruptions'):
            interruptions_count = len(recorder.tracker.interruptions)
        
        # Add successful result
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
        
        # Add failed result
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
    """Main batch processing function"""
    print("📦 Starting Batch Mode")
    print("=" * 50)
    
    # Check ADB connection
    if not check_adb_connection():
        print("❌ No ADB device connected.")
        print("Please connect your Android device and enable USB debugging.")
        return
    
    print("✅ ADB connection verified")
    
    # Select audio files
    audio_files = select_audio_files()
    if not audio_files:
        print("❌ No audio files selected.")
        return
    
    print(f"📁 Selected {len(audio_files)} audio file(s)")
    
    # Initialize components
    recorder = FlawlessRecorder()
    processor = BatchProcessor()
    
    # Ensure output directories exist
    os.makedirs("extracted_audio", exist_ok=True)
    os.makedirs(processor.graphs_folder, exist_ok=True)
    
    # Process each file
    successful_count = 0
    total_start_time = time.time()
    
    for i, file_path in enumerate(audio_files, 1):
        print(f"\n{'='*20} File {i}/{len(audio_files)} {'='*20}")
        
        if process_single_file(file_path, recorder, processor):
            successful_count += 1
        
        # Small delay between files
        if i < len(audio_files):
            print("⏳ Waiting before next file...")
            time.sleep(1)
    
    # Final summary
    total_time = time.time() - total_start_time
    print(f"\n{'='*50}")
    print("📊 BATCH PROCESSING COMPLETE")
    print(f"Total files: {len(audio_files)}")
    print(f"Successful: {successful_count}")
    print(f"Failed: {len(audio_files) - successful_count}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per file: {total_time/len(audio_files):.1f}s")
    
    # Save results and print summary
    try:
        processor.save_results_to_excel()
        print("✅ Results saved to Excel")
    except Exception as e:
        print(f"❌ Failed to save Excel results: {e}")
    
    processor.print_batch_summary()


if __name__ == "__main__":
    run_batch_mode()