# test_imports.py
try:
    import src.facade.program_facade
    print("Successfully imported src.facade.program_facade")
except ImportError as e:
    print(f"Import error: {e}")

try:
    import src.trackers.system_tracker
    print("Successfully imported src.trackers.system_tracker")
except ImportError as e:
    print(f"Import error: {e}")