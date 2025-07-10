#screen_recorder.py

import time
from adb_controller import tap
from device_config_loader import get_device_coords

def start_recording_az():
    coords = get_device_coords()
    tap(coords['ExpandMenuX1'], coords['ExpandMenuY1'])
    time.sleep(1)
    tap(coords['StartAZX'], coords['StartAZY'])
    time.sleep(1.5)
    tap(coords['StartRecX'], coords['StartRecY'])
    time.sleep(1.5)
    tap(coords['ConfirmX'], coords['ConfirmY'])
    time.sleep(1.5)
    tap(coords['MinimizeX'], coords['MinimizeY'])
    time.sleep(2)

def stop_and_save_recording_az():
    coords = get_device_coords()
    tap(coords['ExpandMenuX2'], coords['ExpandMenuY2'])
    time.sleep(2)
    tap(coords['StopX'], coords['StopY'])
    time.sleep(4)
