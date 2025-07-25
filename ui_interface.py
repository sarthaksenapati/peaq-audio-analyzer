from modes.single_mode import run_single_mode
from modes.batch_mode import run_batch_mode
from modes.folder_push_mode import run_folder_push_batch_mode
from modes.manual_comparison_mode import run_manual_comparison_mode
from modes.excel_mode import run_excel_based_testing_mode

def display_main_menu():
    print("\n🎬 Flawless Audio Capture + PEAQ Analyzer")
    print("=" * 60)
    print("Choose a mode:")
    print("  [1] Single File Mode (1 File-Push + Record + Analyze + Report)")
    print("  [2] Batch Mode (Multiple File-Push + Record + Analyze + Report)(Select Files)")
    print("  [3] Folder Push Mode (Folder-Push + Record + Analyze + Report)")
    print("  [4] Manual Comparison (Compares two files already available in the directory)")
    print("  [5] Excel-Driven Testing (Asks for Excel file with test cases and runs them)")
    print("  [6] Spotify Record Mode (Batch Playlist Capture)")
    print("  [7] Spotify Comparison Mode (Folder Matching)")
    return input("> ").strip()


def route_user(choice):
    match choice:
        case '1': run_single_mode()
        case '2': run_batch_mode()
        case '3': run_folder_push_batch_mode()
        case '4': run_manual_comparison_mode()
        case '5': run_excel_based_testing_mode()
        case '6':
            from spotify_mode import main as spotify_record_main
            spotify_record_main()
        case '7':
            from spotify_comparison_mode import run_spotify_comparison_mode
            run_spotify_comparison_mode()
        case _:
            print("❌ Invalid choice. Please select 1–7.")
