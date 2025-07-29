import os

def disable_screen_rotation():
    # Set accelerometer_rotation to 0 (lock rotation)
    os.system('adb shell settings put system accelerometer_rotation 0')
    print("Screen rotation disabled (locked in current orientation).")

def set_max_volume():
    # Set media volume to max by sending VOLUME_UP keyevent multiple times
    for _ in range(30):
        os.system('adb shell input keyevent 24')  # 24 is KEYCODE_VOLUME_UP
    print("Media volume set to maximum.")

def main():
    disable_screen_rotation()
    set_max_volume()

if __name__ == "__main__":
    main()
