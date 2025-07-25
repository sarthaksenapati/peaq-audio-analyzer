import os
import pandas as pd
import subprocess

def parse_duration(duration):
    if isinstance(duration, str) and ':' in duration:
        try:
            minutes, seconds = map(int, duration.strip().split(":"))
            return minutes * 60 + seconds
        except:
            return None
    try:
        return int(float(duration))
    except:
        return None

def split_audio_by_durations(input_audio, excel_path, output_dir):
    df = pd.read_excel(excel_path)
    if "duration" not in df.columns:
        print("❌ Excel file must have a 'duration' column.")
        return

    durations = df["duration"].dropna()

    start_time = 0
    for i, duration in enumerate(durations):
        seconds = parse_duration(duration)
        if seconds is None:
            print(f"❌ Error parsing duration: {duration}")
            continue

        output_filename = os.path.join(output_dir, f"track{i+1}.wav")
        cmd = [
            "ffmpeg", "-y",
            "-i", input_audio,
            "-ss", str(start_time),
            "-t", str(seconds),
            output_filename
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Error splitting track track{i+1}: {result.stderr}")
        else:
            print(f"✅ Saved: {output_filename}")

        start_time += seconds
