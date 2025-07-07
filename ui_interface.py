from modes.single_mode import run_single_mode
from modes.batch_mode import run_batch_mode
from modes.folder_push_mode import run_folder_push_batch_mode
from modes.manual_comparison_mode import run_manual_comparison_mode
from modes.excel_mode import run_excel_based_testing_mode
from device_config_loader import load_coordinates_from_default_file

def display_main_menu():
    print("\n🎬 Flawless Audio Capture + PEAQ Analyzer")
    print("=" * 60)
    print("Choose a mode:")
    print("  [1] Single File Mode(1 File-Push + Record + Analyze + Report)")
    print("  [2] Batch Mode (Multiple File-Push + Record + Analyze + Report)(Select Files)")
    print("  [3] Folder Push Mode (Folder-Push + Record + Analyze + Report)")
    print("  [4] Manual Comparison(Compares two files already available in the directory)")
    print("  [5] Excel-Driven Testing (Asks for Excel file with test cases and runs them)")
    return input("> ").strip()

def route_user(choice):
    if choice in {'1', '2', '3', '4', '5'}:
        # Load device-specific tap coordinates before anything starts
        load_coordinates_from_default_file()


    match choice:
        case '1': run_single_mode()
        case '2': run_batch_mode()
        case '3': run_folder_push_batch_mode()
        case '4': run_manual_comparison_mode()
        case '5': run_excel_based_testing_mode()
        case _: print("❌ Invalid choice. Please select 1-5.")
