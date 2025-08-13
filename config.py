# config.py

# Directories
device_audio_dir = "/sdcard/Music/test_push"  # or whatever path you were using earlier

recording_dir = "/storage/emulated/0/Movies/AzScreenRecorder"
local_pull_dir = "./recordings"
output_audio_dir = "./extracted_audio"
interruption_log_dir = "./interruption_logs"
batch_results_dir = "./batch_results"
batch_graphs_dir = "./batch_graphs"

# Toggles
SHOW_GRAPHS = True
FAST_MODE = False

# PEAQ frame settings
FRAME_SIZE = 1024
HOP_SIZE = 1024 if FAST_MODE else 512

# Audio processing settings
# Fine-tune this value based on your specific setup
TEST_AUDIO_START_DELAY = 0.009  # Try values like 0.008, 0.009, 0.010
ENABLE_AUTO_DELAY_COMPENSATION = True  # Toggle for delay compensation

# Sample-level delay compensation (9ms at 44.1kHz = ~397 samples)
SAMPLE_DELAY_COMPENSATION = int(TEST_AUDIO_START_DELAY * 44100)  # 397 samples at 44.1kHz

selected_audio_device = "Microphone (USB PnP Sound Device)"  # Replace with your actual device name
playback_method = "files"  # or "ytmusic"
spotify_comparison_range = "1-2"  # Use the same format as before

excel_path = r"C:/Users/KIIT/OneDrive/Desktop/timestamps.xlsx"     # Full or relative path to the Excel file
recording_phone = "phone1"                # "phone1" or "phone2"
playback_app = "audible"                  # Choose from: "audible", "gaana", "jiosaavn", "spotify"

selected_mode = "6"  # Replace with "1" to "7" depending on what you want to run
#        case '1': run_single_mode()
#        case '2': run_batch_mode()
#        case '3': run_folder_push_batch_mode()
#        case '4': run_manual_comparison_mode()
#        case '5': run_excel_based_testing_mode()
#        case '6': run_spotify_record_mode()
#        case '7': run_spotify_comparison_mode() 
