# Debug visualization - comment out when not needed
import cv2
fps = 30  # Adjust this to match your video's fps
for frame in result:
    cv2.imshow('Video Playback', frame)
    if cv2.waitKey(int(1000/fps)) & 0xFF == ord('q'):  # Press 'q' to exit
        break
cv2.destroyAllWindows()


###############################################
# @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ #
#                                             #
#     Another debug solution I had to try     #
#                                             #
# @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ @ #
###############################################

  print("FOO\nFOO\nFOO\nFOO\nFOO\nFOO\nFOO\n56ru")
   # If out_vid is a list of frames or numpy arrays
   if isinstance(out_vid, (list, np.ndarray)):
        frames = out_vid
    else:  # If out_vid is a VideoWriter object
        # First release the writer if it's still open
        print("63ru")
        if hasattr(out_vid, 'release'):
            print("release 65ru")
            out_vid.release()

        # Then read from the output file
        output_path = test_out_dir + name
        cap = cv2.VideoCapture(output_path)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()

    # Display frames
    fps = 30
    for frame in frames:
        cv2.imshow('Video Playback', frame)
        key = cv2.waitKey(int(1000/fps))
        if key & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
