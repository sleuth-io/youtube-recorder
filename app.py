import os
import sys
from os import path
from pathlib import Path

import evdev
from obswebsocket import obsws, requests

project_dir = sys.argv[1]
saved_dir = path.join(project_dir, "saved")
Path(saved_dir).mkdir(exist_ok=True)
discarded_dir = path.join(project_dir, "disgarded")
Path(discarded_dir).mkdir(exist_ok=True)

obs = obsws("localhost", 4444, "sleuth")
obs.connect()

device = evdev.InputDevice('/dev/input/event12')


def goodbye():
    _discard_recording(False)


import atexit

atexit.register(goodbye)


def run():

    obs.call(requests.StartRecording())

    with device.grab_context():
        for event in device.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                if event.code == evdev.ecodes.KEY_B and event.value == 1:
                    _save_recording()
                elif event.code == evdev.ecodes.KEY_A and event.value == 1:
                    _discard_recording()


def _discard_recording(restart=True):
    status = obs.call(requests.GetRecordingStatus())
    old_path = status.getRecordingFilename()
    old_file = os.path.basename(old_path)
    _stop()
    rename_path = path.join(discarded_dir, old_file)
    Path(old_path).rename(rename_path)
    if restart:
        _start()
    print(f"Discarded file: {rename_path}")


def _save_recording():
    status = obs.call(requests.GetRecordingStatus())
    old_path = status.getRecordingFilename()
    old_file = os.path.basename(old_path)
    _stop()
    rename_path = path.join(saved_dir, old_file)
    Path(old_path).rename(rename_path)
    _start()
    print(f"Saved file: {rename_path}")


def _stop():
    obs.call(requests.StopRecording())
    while True:
        status = obs.call(requests.GetRecordingStatus())
        if not status.getIsRecording():
            return status


def _start():
    obs.call(requests.StartRecording())
    while True:
        status = obs.call(requests.GetRecordingStatus())
        if status.getIsRecording():
            return status

run()
