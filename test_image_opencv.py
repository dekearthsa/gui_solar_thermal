import cv2
import time

def main():
    # Desired Frames Per Second
    DESIRED_FPS = 10
    FRAME_DURATION = 1.0 / DESIRED_FPS  # Duration of each frame in seconds

    # Initialize video capture (0 for the default webcam)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    # Optionally, set the camera's frame rate if supported
    cap.set(cv2.CAP_PROP_FPS, DESIRED_FPS)

    while True:
        loop_start_time = time.time()

        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame.")
            break

        # Prepare FPS text (fixed at DESIRED_FPS)
        fps_text = f"FPS: {DESIRED_FPS}"

        # Choose font, scale, color, and thickness
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (0, 255, 0)  # Green color in BGR
        thickness = 2

        # Position for the FPS text
        position = (10, 30)  # Top-left corner

        # Overlay FPS on the frame
        cv2.putText(frame, fps_text, position, font, font_scale, color, thickness, cv2.LINE_AA)

        # Display the resulting frame
        cv2.imshow('Video with Fixed FPS', frame)

        # Calculate elapsed time and determine sleep duration
        loop_end_time = time.time()
        elapsed_time = loop_end_time - loop_start_time
        sleep_time = FRAME_DURATION - elapsed_time

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            # Processing is taking longer than FRAME_DURATION
            # You might want to handle this case (e.g., skip frames, log a warning)
            pass

        # Exit when 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the capture and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
