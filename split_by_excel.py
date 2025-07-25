import os
import pandas as pd
from pydub import AudioSegment

def split_audio_by_excel(full_audio_path, excel_path, output_folder, suffix="phone1"):
    audio = AudioSegment.from_file(full_audio_path)
    df = pd.read_excel(excel_path)

    current_pos = 0  # in milliseconds

    for _, row in df.iterrows():
        name = str(row['track_name'])
        duration = float(row['duration (in seconds)'])
        end_pos = current_pos + int(duration * 1000)

        segment = audio[current_pos:end_pos]
        out_name = f"{name}_{suffix}.wav"
        out_path = os.path.join(output_folder, out_name)
        segment.export(out_path, format="wav")

        print(f"🎧 Saved: {out_path}")
        current_pos = end_pos
