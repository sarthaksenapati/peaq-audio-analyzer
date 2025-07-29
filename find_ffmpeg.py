import os
import sys
from pathlib import Path

# Common places to search for ffmpeg on Windows
COMMON_DIRS = [
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin",
    r"C:\Program Files (x86)\ffmpeg\bin",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    str(Path.home()),
    os.getcwd(),
]

# Recursively search for ffmpeg.exe in a directory
def find_ffmpeg_in_dir(root_dir):
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower() == "ffmpeg.exe":
                matches.append(os.path.join(dirpath, filename))
    return matches

def main():
    found = []
    print("🔍 Scanning for ffmpeg.exe in common locations...")
    for d in COMMON_DIRS:
        if os.path.exists(d):
            found += find_ffmpeg_in_dir(d)

    # Also check PATH
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.exists(p):
            found += find_ffmpeg_in_dir(p)

    # Remove duplicates
    found = list(dict.fromkeys(found))

    if not found:
        print("❌ ffmpeg.exe not found in common locations or PATH.")
        print("You may need to download it from https://ffmpeg.org/download.html")
        return

    print(f"\n✅ Found {len(found)} ffmpeg.exe file(s):\n")
    for idx, path in enumerate(found):
        print(f"[{idx+1}] {path}")
        print(f"    - To add to PATH: {os.path.dirname(path)}")
        print(f"    - To use in code: {path}")

    print("\nAdd the directory above to your PATH environment variable.")
    print("Or, use the full path above as ffmpeg_path in your Python code.")

if __name__ == "__main__":
    main()
