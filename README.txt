PEAQ Audio Analyzer
===================

A powerful Python-based audio evaluation tool that records, aligns, and analyzes audio for perceptual quality using the PEAQ standard. This system supports multiple modes of operation including batch and folder-based testing. It also integrates automated push-play-record cycles and Excel-based configuration for tap-based audio control.

Project Structure
-----------------
donut/
├── assets/                    # Contains test assets and sample data
├── temp/                      # Temporary files generated during processing
├── main.py                    # Main script for launching the tool
├── modes/                     # Different modes of analysis (single, batch, folder, excel, etc.)
├── analysis/                  # Core PEAQ analysis logic
├── utils/                     # Utility modules (alignment, conversion, UI handling)
├── tap_config.xlsx            # Excel configuration for tap-based automation
├── requirements.txt           # Python dependencies
└── README.txt                 # Project documentation

Features
--------
- Multiple Modes:
  - Single File Mode: Push, Record, Analyze, Report
  - Batch Mode: Analyze multiple selected files
  - Folder Mode: Analyze all files in a folder
  - Excel Automation Mode: Read tap commands from Excel
  - Files App Mode: Playback from Files app with automated trimming

- Automatic Alignment:
  - Uses cross-correlation to perfectly align recorded and reference signals before analysis

- PEAQ Analysis:
  - Full implementation of perceptual quality scoring using ITU-R BS.1387 standards

- Mobile Integration:
  - Supports tap-based automation and playback through Android/iOS Files apps

- Smart Trimming:
  - Automatically trims silence using known tap offsets and durations
  - Optional buffer to prevent premature cut-off

- Visual & Textual Reports:
  - Generates waveform comparisons and CSV/Excel reports

Installation
------------
1. Clone the Repository

   git clone https://github.com/sarthaksenapati/peaq-audio-analyzer.git
   cd peaq-audio-analyzer

2. Set Up Environment

   pip install -r requirements.txt

   Note: Ensure `ffmpeg.exe` is available in your system PATH. FFMPEG is required for format conversions. Native Python libraries alone cannot handle all audio formats.
   Download FFMPEG from https://ffmpeg.org/download.html

Usage
-----
Run the main program:

   python main.py

Select the desired mode from the menu:

   Flawless Audio Capture + PEAQ Analyzer
   ============================================
   Choose a mode:
     [1] Single File Mode
     [2] Batch Mode (Multiple Files)
     [3] Folder Push Mode
     [4] Excel Tap Mode
     [5] Files App Mode (Tap + Auto Trim)

Important: Always start recording before the playback tap when using automation. The system uses known tap delays to align and trim automatically.

Excel Configuration (Tap Mode)
------------------------------
Use the `tap_config.xlsx` to configure tap coordinates and expected durations. The system will use these for UI automation and trimming logic.

FFMPEG Security Note
--------------------
Although `ffmpeg.exe` is widely used, it is a third-party executable. For improved safety:
- Sandbox ffmpeg if required
- Use a local, verified copy only
- The program does not invoke it unless conversion is needed

Supported Formats
-----------------
By default:
- `.wav` is supported natively
- For `.mp3`, `.m4a`, `.aac`, etc., `ffmpeg` is required

Current Status
--------------
All 5 core modes are tested and fully operational:
- Alignment logic is fixed
- Excel reading for tap configuration works reliably
- Files App-based automation is tested and consistent

Contact
-------
Developed and maintained by Sarthak Senapati
https://github.com/sarthaksenapati
