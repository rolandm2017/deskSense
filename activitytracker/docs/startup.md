# To start the regular server:

deskSense\surveillance> uvicorn src.surveillance.server:app --reload

# To start peripheral tracking:

deskSense> cd .\surveillance\
deskSense\surveillance> .\.venv\Scripts\activate
(.venv) PS C:\deskSense\surveillance> python .\surveillance\peripherals.py
