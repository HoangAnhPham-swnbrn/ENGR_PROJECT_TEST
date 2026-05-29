from picamera2 import Picamera2
import cv2
import numpy as np
import time

picam2 = Picamera2()

config = picam2.create_video_configuration(
    main={"format": "XRGB8888", "size": (640, 480)},
    controls={
        "FrameRate": 90,
        "Sharpness": 1.5,
        "Contrast": 1.1,
        "Brightness": 0.0,
        "AwbMode": 0,
        "AeEnable": True,
        "NoiseReductionMode": 1,
    },
    buffer_count=6
)

picam2.configure(config)
picam2.start()
time.sleep(2)

frame_count = 0
fps_display = 0
prev_time = time.time()

while True:
    frame = picam2.capture_array()

    # Fix — make contiguous array OpenCV can work with
    frame_bgr = np.ascontiguousarray(frame[:, :, :3])

    # FPS counter
    frame_count += 1
    if frame_count % 15 == 0:
        curr_time = time.time()
        fps_display = 15 / (curr_time - prev_time)
        prev_time = curr_time

    cv2.putText(frame_bgr, f"FPS: {fps_display:.0f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Camera", frame_bgr)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

picam2.stop()
cv2.destroyAllWindows()
