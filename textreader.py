import os
import xml.etree.ElementTree as ET
import time

def launch_spotify():
    print("Launching Spotify app...")
    os.system('adb shell monkey -p com.spotify.music -c android.intent.category.LAUNCHER 1')
    time.sleep(4)

def find_text_bounds(xml_file, target_text=None, resource_id=None, content_desc=None):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for node in root.iter('node'):
        if resource_id and node.attrib.get('resource-id') == resource_id:
            bounds = node.attrib.get('bounds')
            if bounds:
                x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
                x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
                return (x1 + x2) // 2, (y1 + y2) // 2
        if content_desc and node.attrib.get('content-desc') == content_desc:
            bounds = node.attrib.get('bounds')
            if bounds:
                x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
                x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
                return (x1 + x2) // 2, (y1 + y2) // 2
        if target_text and (node.attrib.get('text') == target_text or (node.attrib.get('content-desc') and target_text in node.attrib.get('content-desc'))):
            bounds = node.attrib.get('bounds')
            if bounds:
                x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
                x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
                return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def find_shuffle_play_button(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for node in root.iter('node'):
        node_class = node.attrib.get('class', '')
        content_desc = node.attrib.get('content-desc', '')
        clickable = node.attrib.get('clickable') == 'true'
        bounds = node.attrib.get('bounds')
        if (
            node_class == 'android.widget.Button'
            and content_desc == 'Play playlist'
            and clickable
            and bounds
        ):
            x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
            x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
            return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def find_shuffle_play_button(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for node in root.iter('node'):
        node_class = node.attrib.get('class', '')
        content_desc = node.attrib.get('content-desc', '')
        clickable = node.attrib.get('clickable') == 'true'
        bounds = node.attrib.get('bounds')
        if (
            node_class == 'android.widget.Button'
            and content_desc == 'Play playlist'
            and clickable
            and bounds
        ):
            x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
            x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
            return (x1 + x2) // 2, (y1 + y2) // 2
    return None
    tree = ET.parse(xml_file)
    root = tree.getroot()
    for node in root.iter('node'):
        if resource_id and node.attrib.get('resource-id') == resource_id:
            bounds = node.attrib.get('bounds')
            if bounds:
                x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
                x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
                return (x1 + x2) // 2, (y1 + y2) // 2
        if content_desc and node.attrib.get('content-desc') == content_desc:
            bounds = node.attrib.get('bounds')
            if bounds:
                x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
                x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
                return (x1 + x2) // 2, (y1 + y2) // 2
        if target_text and (node.attrib.get('text') == target_text or (node.attrib.get('content-desc') and target_text in node.attrib.get('content-desc'))):
            bounds = node.attrib.get('bounds')
            if bounds:
                x1, y1 = map(int, bounds.split('][')[0][1:].split(','))
                x2, y2 = map(int, bounds.split('][')[1][:-1].split(','))
                return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def tap_by_text(text):
    os.system('adb shell uiautomator dump /sdcard/ui.xml')
    os.system('adb pull /sdcard/ui.xml .')
    coords = find_text_bounds('ui.xml', target_text=text)
    if coords:
        x, y = coords
        print(f"Tapping {text} at ({x},{y})")
        os.system(f'adb shell input tap {x} {y}')
    else:
        print(f"Text '{text}' not found on screen.")



def tap_play_button():
    os.system('adb shell uiautomator dump /sdcard/ui.xml')
    os.system('adb pull /sdcard/ui.xml .')
    coords = find_shuffle_play_button('ui.xml')
    if coords:
        x, y = coords
        print(f"Tapping green Shuffle Play button at ({x},{y})")
        os.system(f'adb shell input tap {x} {y}')
        return
    coords = find_text_bounds('ui.xml', resource_id="com.spotify.music:id/play_pause_button")
    if not coords:
        coords = find_text_bounds('ui.xml', content_desc="Play")
    if coords:
        x, y = coords
        print(f"Tapping Play button at ({x},{y})")
        os.system(f'adb shell input tap {x} {y}')
    else:
        print("Play button not found by resource-id or content-desc. Trying keyevent 126...")
        os.system('adb shell input keyevent 126')

# Launch Spotify
launch_spotify()
# Tap 'Your Library' and 'Liked Songs' by text
tap_by_text("Your Library")
tap_by_text("Liked Songs")
# Robust Play button tap using resource-id/content-desc
tap_play_button()