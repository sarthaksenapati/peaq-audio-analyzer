import os
import xml.etree.ElementTree as ET
import time

def adb_prefix(adb_serial):
    return f"adb -s {adb_serial}" if adb_serial else "adb"

def launch_jiosaavn(adb_serial=None):
    print("Launching JioSaavn app...")
    cmd = f"{adb_prefix(adb_serial)} shell monkey -p com.jio.media.jiobeats -c android.intent.category.LAUNCHER 1"
    os.system(cmd)
    time.sleep(4)

def find_text_bounds(xml_file, target_text=None, resource_id=None, content_desc=None):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for node in root.iter('node'):
        if resource_id and node.attrib.get('resource-id') == resource_id:
            bounds = node.attrib.get('bounds')
        elif content_desc and node.attrib.get('content-desc') == content_desc:
            bounds = node.attrib.get('bounds')
        elif target_text and (node.attrib.get('text') == target_text or (node.attrib.get('content-desc') and target_text in node.attrib.get('content-desc'))):
            bounds = node.attrib.get('bounds')
        else:
            continue
        if bounds:
            x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
            x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
            return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def tap_by_text(text, adb_serial=None):
    os.system(f"{adb_prefix(adb_serial)} shell uiautomator dump /sdcard/ui.xml")
    os.system(f"{adb_prefix(adb_serial)} pull /sdcard/ui.xml .")
    coords = find_text_bounds('ui.xml', target_text=text)
    if coords:
        x, y = coords
        print(f"Tapping {text} at ({x},{y})")
        os.system(f"{adb_prefix(adb_serial)} shell input tap {x} {y}")
    else:
        print(f"Text '{text}' not found on screen.")

def tap_play_button_jiosaavn(adb_serial=None):
    import math
    os.system(f"{adb_prefix(adb_serial)} shell uiautomator dump /sdcard/ui.xml")
    os.system(f"{adb_prefix(adb_serial)} pull /sdcard/ui.xml .")
    # Try by resource-id first
    coords = find_text_bounds('ui.xml', resource_id="com.jio.media.jiobeats:id/2131362155")
    if coords:
        x, y = coords
        print(f"Tapping blue Play button at ({x},{y})")
        os.system(f"{adb_prefix(adb_serial)} shell input tap {x} {y}")
        return

    # Fallback: find clickable android.view.View closest to (942,906)
    tree = ET.parse('ui.xml')
    root = tree.getroot()
    target_x, target_y = 942, 906
    min_dist = float('inf')
    best_coords = None
    best_bounds = None
    for node in root.iter('node'):
        if node.attrib.get('class') == 'android.view.View' and node.attrib.get('clickable') == 'true':
            bounds = node.attrib.get('bounds')
            if bounds:
                x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
                x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                dist = math.hypot(cx - target_x, cy - target_y)
                if dist < min_dist:
                    min_dist = dist
                    best_coords = (cx, cy)
                    best_bounds = bounds
    if best_coords:
        x, y = best_coords
        print(f"Tapping play button (class=android.view.View, clickable, bounds={best_bounds}) at ({x},{y})")
        os.system(f"{adb_prefix(adb_serial)} shell input tap {x} {y}")
    else:
        print("Play button not found robustly, trying keyevent 126...")
        os.system(f"{adb_prefix(adb_serial)} shell input keyevent 126")

def launch_and_play_jiosaavn_playlist(adb_serial=None):
    launch_jiosaavn(adb_serial=adb_serial)
    tap_by_text("My Library", adb_serial=adb_serial)
    tap_by_text("Playlists", adb_serial=adb_serial)
    tap_by_text("random", adb_serial=adb_serial)
    tap_play_button_jiosaavn(adb_serial=adb_serial)

if __name__ == "__main__":
    launch_and_play_jiosaavn_playlist()