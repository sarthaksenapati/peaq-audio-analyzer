import os
import subprocess

# List all audio files in the given directory that have .wav or .mp3 extensions
def list_audio_files(directory):
    files = [f for f in os.listdir(directory) if f.lower().endswith(('.wav', '.mp3'))]
    return files

# Prompt user to select a file from the list, with validation
def select_file(files, prompt):
    for i, file in enumerate(files):
        print(f"{i + 1}. {file}")  # Show index and filename
    while True:
        try:
            idx = int(input(prompt))  # Get user input
            if 1 <= idx <= len(files):
                return files[idx - 1]
            else:
                print("Invalid selection. Choose a valid number.")
        except ValueError:
            print("Please enter a number.")

# Main function to orchestrate file selection and run the PEAQ test script
def main():
    directory = '.'  # Set the directory to look for audio files (current folder)
    audio_files = list_audio_files(directory)
    
    if len(audio_files) < 2:
        print("Need at least two audio files to compare.")
        return

    # Step 1: Select reference file
    print("Select Reference Audio File:")
    ref_file = select_file(audio_files, "Enter number for reference file: ")

    # Step 2: Select test file (can even be the same file for ODG = 0 check)
    print("\nSelect Test Audio File (you may pick the same file to test ODG=0):")
    test_file = select_file(audio_files, "Enter number for test file: ")

    # Step 3: Construct the command to call the main analysis script
    cmd = ['python', 'test_peaq.py', ref_file, test_file]
    print(f"\nRunning: {' '.join(cmd)}\n")

    # Step 4: Execute the PEAQ comparison using subprocess
    subprocess.run(cmd)

# Entry point
if __name__ == "__main__":
    main()
