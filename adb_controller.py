# adb_controller.py

import subprocess
import time
import os
def run_adb(cmd):
    return subprocess.run(["adb"] + cmd, capture_output=True, text=True).stdout.strip()

def adb_shell(cmd):
    return run_adb(["shell"] + cmd)

def check_adb_connection():
    try:
        devices = run_adb(["devices"])
        device_lines = [line for line in devices.split('\n') if 'device' in line and not line.startswith('List')]
        return bool(device_lines)
    except Exception:
        return False

def tap(x, y):
    subprocess.run(["adb", "shell", "input", "tap", str(x), str(y)])

def push_audio(file_path):
    filename = file_path.split("/")[-1]
    print(f"📤 Pushing '{filename}' to device...")
    run_adb(["push", file_path, f"/sdcard/{filename}"])

def list_recordings():
    out = run_adb(["shell", "ls", "/sdcard/Movies/AzScreenRecorder"])
    return out.splitlines() if out else []

def pull_recording(filename):
    target = f"/sdcard/Movies/AzScreenRecorder/{filename}"
    output_dir = "./recordings"
    os.makedirs(output_dir, exist_ok=True)
    output = os.path.join(output_dir, filename)
    run_adb(["pull", target, output])
    return output

