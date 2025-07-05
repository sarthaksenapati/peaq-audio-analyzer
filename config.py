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

