
def log_finish_video(frame_count, output_vid_name, current_index):
    print("[LOG] Ending on frame " + str(frame_count) +
          " for video " + output_vid_name)
    print(f"[LOG] Completed video segment {current_index-1}")


def log_ending(frame_count, vid_name):
    print("[LOG] Ending on frame " + str(frame_count) +
          " for video " + vid_name)
