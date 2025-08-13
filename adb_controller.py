# adb_controller.py

import subprocess
import os
import threading
import time

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
    filename = os.path.basename(file_path)
    print(f"📤 Pushing '{filename}' to device...")
    run_adb(["push", file_path, f"/sdcard/{filename}"])

def keep_phone_awake():
    # Prevent the phone from sleeping by setting the stay_on_while_plugged_in setting
    os.system('adb shell settings put global stay_on_while_plugged_in 3')
    print("Phone is set to stay awake while charging.")

    # Periodically simulate user activity to keep the screen on
    def simulate_user_activity():
        while True:
            os.system('adb shell input keyevent 224')  # 224 is KEYCODE_WAKEUP
            time.sleep(300)  # Repeat every 5 minutes

    # Start the thread to simulate user activity
    threading.Thread(target=simulate_user_activity, daemon=True).start()
