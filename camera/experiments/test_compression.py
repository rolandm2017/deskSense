# # test_compression.py
# import os
# import time
# from src.compression import convert_for_ml, VideoConverter

# start_file = "fodder/output1.avi"

# if not os.path.exists(start_file):
#     raise FileNotFoundError(f"Input video file not found: {start_file}")
# if not start_file.endswith('.avi'):
#     raise ValueError(f"Input file must be .avi format: {start_file}")


# dest = "fodder/out1_sml.avi"


# def on_finish(v):
#     print("Done")


# def main():
#     converter = VideoConverter(start_file, dest, on_finish)
#     converter.start()

#     # Keep main thread alive
#     while converter.is_alive():
#         time.sleep(0.1)  # Or time.sleep(0.1) to reduce CPU usage


# if __name__ == "__main__":
#     main()
