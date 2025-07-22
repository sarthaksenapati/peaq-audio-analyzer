from file_manager_playback import play_via_files_app
from yt_music_playback import play_via_yt_music

def choose_playback_method():
    print("\n🎛️ Choose playback method:")
    print("1. Files app (tap-based)")
    print("2. YT Music (intent-based)")
    choice = input("Enter 1 or 2: ")

    if choice == "1":
        return play_via_files_app
    elif choice == "2":
        return play_via_yt_music
    else:
        print("Invalid choice. Defaulting to YT Music.")
        return play_via_yt_music
