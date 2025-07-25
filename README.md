# Marvel Audio Automation Suite

This project provides tools for automated audio capture, splitting, and quality analysis for music streaming apps (Spotify, Audible, Gaana, JioSaavn) on Android devices. It is designed for batch testing and comparison of audio quality using Excel-driven playlists and PEAQ analysis.

## Main Components

### 1. `spotify_mode.py`
- **Purpose:** Automates recording of a playlist from a selected app (Spotify, Audible, Gaana, JioSaavn) and splits the recording into tracks based on durations from an Excel file.
- **Workflow:**
  1. Prompts user to select an Excel file with a `duration` column (in seconds or MM:SS).
  2. Sums total duration for recording.
  3. Lets user select an audio input device (e.g., stereo mix, loopback).
  4. Asks which app to launch for playback.
     - For Spotify, uses ADB keyevent 126 (Play) to start and 127 (Pause) to stop.
     - For other apps, uses keyevent 85 (Toggle Play/Pause).
  5. Records the audio using FFmpeg, overwriting any previous output.
  6. Splits the recording into individual tracks as per the Excel durations, overwriting any previous tracks folder.

### 2. `spotify.py`
- **Purpose:** Provides utility functions for launching apps, sending ADB keyevents, and listing audio input devices.
- **Key Functions:**
  - `launch_spotify`, `launch_audible`, `launch_gaana`, `launch_jiosaavn`: Launch the respective app on the connected Android device.
  - `adb(cmd)`: Runs an ADB shell command and returns output.
  - `list_audio_input_devices()`: Lists available audio input devices for FFmpeg.

### 3. `spotify_comparison_mode.py`
- **Purpose:** Compares the split tracks from two phones (e.g., `phone1_tracks` vs `phone2_tracks`) using PEAQ audio quality analysis.
- **Workflow:**
  1. Looks for `phone1_tracks` and `phone2_tracks` folders.
  2. For each matching file, runs PEAQ comparison and logs ODG (Objective Difference Grade) and quality.
  3. Saves results and summary to Excel.

## How to Use

1. **Prepare your playlist and durations Excel file.**
   - The Excel file must have a `duration` column (in seconds or MM:SS).

2. **Connect your Android device with ADB enabled.**

3. **Run `spotify_mode.py`**
   - Follow prompts to select Excel, audio device, phone, and app.
   - The script will record, split, and save tracks in a folder (e.g., `phone1_tracks`).
   - Existing tracks and output files are automatically overwritten.

4. **Repeat for the second phone if needed.**

5. **Run `spotify_comparison_mode.py`**
   - Compares tracks from both phones and generates a quality report.

## Notes
- For Spotify, only keyevent 126 (Play) and 127 (Pause) work reliably for playback control.
- For other apps, keyevent 85 (Toggle Play/Pause) is used.
- If automation fails, you may need to manually press play in the app.
- All output files and folders are overwritten each run for convenience.

## Requirements
- Python 3.x
- FFmpeg installed and in PATH
- ADB installed and in PATH
- Required Python packages: pandas, openpyxl, tkinter

## Troubleshooting
- If playback does not start, try manually pressing play in the app.
- Ensure your audio input device is set up to capture system or loopback audio.
- Make sure your Android device is detected by ADB (`adb devices`).

---

For more details, see comments in each script.
