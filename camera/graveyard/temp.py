# def run_recording_process():
#     while True:
#         ret, frame = capture.read()
#         if interrupt_called:
#             shutdown(capture, output_vid)
#         if ret:
#             frame_count += 1
#             frame = add_timestamp(frame)
#             output_vid.write(frame)

#             # TODO: detect whether I am present in the screen or not using um, um, motion detection

#             current = datetime.now()
#             if current.second != last_second:
#                 print(f"{current.minute:02d}:{current.second:02d}")
#                 last_second = current.second

#             # Check if we've reached 30 seconds (0.5 minutes)
#             if frame_count > frames_per_segment:
#                 log_finish_video(frame_count, output_vid_name, current_index)
#                 output_vid.release()
#                 current_index += 1

#                 # Cleanup starting circumstances
#                 start_time = time.time()  # Reset timer
#                 frame_count = 0  # Reset frame count

#                 compress_finished_vid(output_vid_name, send_to_castle)
#                 # to_be_compressed = output_vid_name
#                 # compressed_out_name = get_compressed_name_for_vid(output_vid_name)
#                 # converter = VideoConverter(to_be_compressed, compressed_out_name)
#                 # converter.start()

#                 # Update video name for next round
#                 output_vid_name = name_new_vid(
#                     base_name, current_index, video_ending)
#                 # Update for next loop
#                 output_vid = initialize_new_vid(output_vid_name)
