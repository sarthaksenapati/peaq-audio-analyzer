import os
from pathlib import Path

# Common places to search for adb on Windows
COMMON_DIRS = [
    r"C:\platform-tools",
    r"C:\Program Files\platform-tools",
    r"C:\Program Files (x86)\platform-tools",
    r"C:\Android\platform-tools",
    r"C:\Program Files\Android\platform-tools",
    r"C:\Program Files (x86)\Android\platform-tools",
    str(Path.home()),
    os.getcwd(),
]

# Recursively search for adb.exe in a directory
def find_adb_in_dir(root_dir):
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower() == "adb.exe":
                matches.append(os.path.join(dirpath, filename))
    return matches

def main():
    found = []
    print("🔍 Scanning for adb.exe in common locations...")
    for d in COMMON_DIRS:
        if os.path.exists(d):
            found += find_adb_in_dir(d)

    # Also check PATH
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.exists(p):
            found += find_adb_in_dir(p)

    # Remove duplicates
    found = list(dict.fromkeys(found))

    if not found:
        print("❌ adb.exe not found in common locations or PATH.")
        print("You may need to download it from https://developer.android.com/studio/releases/platform-tools")
        return

    print(f"\n✅ Found {len(found)} adb.exe file(s):\n")
    for idx, path in enumerate(found):
        print(f"[{idx+1}] {path}")
        print(f"    - To add to PATH: {os.path.dirname(path)}")
        print(f"    - To use in code: {path}")

    print("\nAdd the directory above to your PATH environment variable.")
    print("Or, use the full path above as the adb command in your Python code if needed.")

if __name__ == "__main__":
    main()
