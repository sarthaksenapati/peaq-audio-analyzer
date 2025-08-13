import multiprocessing
import threading
import time
from spotify_mode import main as record_for_device
from spotify import list_audio_input_devices
from multi import get_adb_devices

def run_device_thread(phone_label, audio_device, app_choice, adb_serial):
    print(f"Starting process for {phone_label}...")
    record_for_device(phone_label, audio_device, app_choice, adb_serial)

def main():
    devices = get_adb_devices()
    if len(devices) < 1:
        print("❌ No ADB devices found.")
        return

    print("\nConnected ADB devices:")
    for idx, serial in enumerate(devices):
        print(f"[{idx}] {serial}")

    num_devices = 2  # Set the number of devices manually
    phone_serials = {
        "phone1": devices[0],
        "phone2": devices[1] if len(devices) > 1 else None,
    }

    audio_devices = list_audio_input_devices()
    print("\n🎤 Available Audio Devices:")
    for idx, name in enumerate(audio_devices):
        print(f"[{idx}] {name}")

    audio_device_indices = {
        "phone1": 1,  # Set the audio device index manually for phone1
        "phone2": 2,  # Set the audio device index manually for phone2
    }

    app_choices = {
        "phone1": "spotify",  # Set the app choice manually for phone1
        "phone2": "spotify",  # Set the app choice manually for phone2
    }

    processes = []
    for phone_label in sorted(phone_serials.keys()):
        adb_serial = phone_serials[phone_label]
        audio_idx = audio_device_indices[phone_label]
        audio_device = audio_devices[audio_idx]
        app_choice = app_choices[phone_label]
        p = multiprocessing.Process(
            target=run_device_thread,
            args=(phone_label, audio_device, app_choice, adb_serial)
        )
        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    print("\nAll device recordings and splits complete.")

if __name__ == "__main__":
    main()