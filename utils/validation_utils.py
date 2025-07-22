# utils/validation_utils.py

import os

# Supported audio extensions for general validation
SUPPORTED_AUDIO_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg', '.wma', '.webm', '.opus'}

def validate_audio_file(path):
    """Check if the file exists and has a supported audio extension."""
    return os.path.isfile(path) and os.path.splitext(path)[1].lower() in SUPPORTED_AUDIO_EXTENSIONS
