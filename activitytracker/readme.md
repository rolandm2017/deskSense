# surveillance: what is this?

it's a program that tracks which programs I use on Windows and Ubuntu. how do I spend my time?

## Setup for the activityTracker server

- make a virtual environment
- enter the venv
- run "pip install -r .\windows-requirements.txt"
- OR on linux, run "pip install -r .\requirements.txt

cd C:\Users\roly\Code\desksense\activitytracker
pip install -e .

- populate the virual env. variables:

SYNCHRONOUS_DB_URL=
ASYNC_DATABASE_URL=

SYNC_TEST_DB_URL
ASYNC_TEST_DB_URL

UBUNTU_KEYBOARD_PATH=
UBUNTU_MOUSE_PATH=

MOUSE_KEYBOARD_PATH
WINDOWS_MOUSE_PATH

LOCAL_TIME_ZONE
LOCAL_TIME_OFFSET
LOCAL_TIME_OFFSET_DST

- install pywin32 (not inclueded in requirements.txt so far)

(.desk) PS C:\Users\roly\Code\desksense\activitytracker> python src/activitytracker/server.py

## Setup for the peripherals

