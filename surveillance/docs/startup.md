# To start the regular server:

-   Have the venv activated

PS C:\Users\User\Code\deskSense\surveillance> uvicorn surveillance.server:app --reload

# To start peripheral tracking:

PS C:\Users\User\Code\deskSense> cd .\surveillance\
PS C:\Users\User\Code\deskSense\surveillance> .\.venv\Scripts\activate
(.venv) PS C:\Users\User\Code\deskSense\surveillance> python .\surveillance\peripherals.py

### Or on linux:

~/Code/deskSense/surveillance$ python -m surveillance.peripherals
