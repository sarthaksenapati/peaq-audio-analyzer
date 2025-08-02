from file_manager_playback import play_via_files_app
from yt_music_playback import play_via_yt_music
from config import playback_method  # <-- new import

def choose_playback_method():
    if playback_method.lower() == "files":
        print("✅ Using Files app for playback.")
        return play_via_files_app
    elif playback_method.lower() == "ytmusic":
        print("✅ Using YouTube Music for playback.")
        return play_via_yt_music
    else:
        print(f"⚠️ Invalid playback_method '{playback_method}' in config. Defaulting to YT Music.")
        return play_via_yt_music
