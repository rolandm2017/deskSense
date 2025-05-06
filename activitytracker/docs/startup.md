# To start the regular server:

deskSense\activitytracker> uvicorn src.activitytracker.server:app --reload

# To start peripheral tracking:

deskSense> cd .\activitytracker\
deskSense\activitytracker> .\.venv\Scripts\activate
(.venv) PS C:\deskSense\activitytracker> python .\src\activitytracker\run_peripherals.py
