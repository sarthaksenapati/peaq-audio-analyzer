import subprocess
import os
import datetime

def record_aux_audio(duration=15, device_name="Internal AUX Jack (Steam Streaming Speakers)"):
    # Auto-generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"aux_recording_{timestamp}.wav"
    
    print(f"🎤 Starting AUX recording for {duration} seconds...")
    
    try:
        subprocess.run([
            "ffmpeg",
            "-y",  # Overwrite output if exists
            "-f", "dshow",
            "-i", f"audio={device_name}",
            "-t", str(duration),
            output_filename
        ], check=True)
        
        print(f"✅ Recording complete. Saved as: {output_filename}")
        
    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg failed to record. Make sure your AUX input is working.")
        print("Error details:", e)

if __name__ == "__main__":
    record_aux_audio(duration=15)
