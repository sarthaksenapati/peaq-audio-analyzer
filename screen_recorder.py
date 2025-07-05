# screen_recorder.py

import time
from adb_controller import tap

def start_recording_az():
    tap(1043, 1188)  # expand menu
    time.sleep(1)
    tap(932, 992)    # start AZ
    time.sleep(1.5)
    tap(563, 1105)   # start recorder
    time.sleep(1.5)
    tap(563, 1331)   # confirm
    time.sleep(1.5)
    tap(862, 1764)   # minimize or home
    time.sleep(2)

def stop_and_save_recording_az():
    tap(1043, 1188)  # expand menu
    time.sleep(2)
    tap(837, 1191)   # stop
    time.sleep(4)
