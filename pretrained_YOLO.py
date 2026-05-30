from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import numpy as np
import time

# ── Model ──
model = YOLO("yolov8n.pt")

# ── Victorian road rule relevant classes ──
TRAFFIC_CLASSES = {
    0:  "person",
    1:  "bicycle",
    2:  "car",
    3:  "motorcycle",
    5:  "bus",
    6:  "train",
    7:  "truck",
    9:  "traffic light",
    11: "stop sign",
    12: "parking meter",
}

# Danger level per class (for dashboard alert priority)
DANGER_LEVEL = {
    0:  "high",    # person — pedestrian, highest priority
    1:  "medium",  # bicycle
    2:  "medium",  # car
    3:  "medium",  # motorcycle
    5:  "medium",  # bus
    6:  "low",     # train — unlikely but included
    7:  "medium",  # truck
    9:  "high",    # traffic light — must obey
    11: "high",    # stop sign — must obey
    12: "low",     # parking meter
}

# BGR colours per danger level
DANGER_COLORS = {
    "high":   (0, 0, 255),     # red
    "medium": (0, 165, 255),   # orange
    "low":    (0, 255, 255),   # yellow
}

# ── Confidence thresholds per class ──
# Lower for signs (smaller in frame), higher for vehicles
CONFIDENCE_THRESHOLDS = {
    0:  0.50,   # person
    1:  0.45,   # bicycle
    2:  0.45,   # car
    3:  0.45,   # motorcycle
    5:  0.45,   # bus
    6:  0.40,   # train
    7:  0.45,   # truck
    9:  0.40,   # traffic light — detect early
    11: 0.40,   # stop sign — detect early
    12: 0.40,   # parking meter
}

# ── Camera ──
picam2 = Picamera2()
picam2.configure(
    picam2.create_video_configuration(
        main={"format": "XRGB8888", "size": (640, 480)},
        controls={
            "FrameRate": 30,
            "Sharpness": 1.5,
            "NoiseReductionMode": 1,
            "AeEnable": True,
            "AwbMode": 0,
        },
        buffer_count=4
    )
)
picam2.start()
time.sleep(2)

def draw_lane_lines(frame):
    """
    Detect and draw lane lines using Hough transform.
    Splits frame into left and right halves.
    Returns frame with lanes drawn + lane status dict.
    """
    h, w = frame.shape[:2]
    roi_top = int(h * 0.55)   # only look at bottom 45% of frame

    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur  = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    # Mask to region of interest
    mask = np.zeros_like(edges)
    roi  = np.array([[
        (int(w*0.05), h),
        (int(w*0.45), roi_top),
        (int(w*0.55), roi_top),
        (int(w*0.95), h)
    ]], dtype=np.int32)
    cv2.fillPoly(mask, roi, 255)
    masked = cv2.bitwise_and(edges, mask)

    lines = cv2.HoughLinesP(
        masked, 1, np.pi/180,
        threshold=30,
        minLineLength=40,
        maxLineGap=80
    )

    left_detected  = False
    right_detected = False

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 == x1:
                continue
            slope = (y2 - y1) / (x2 - x1)
            # Left lane: negative slope, left half
            if slope < -0.3 and x1 < w // 2:
                cv2.line(frame, (x1,y1), (x2,y2), (255, 100, 0), 2)
                left_detected = True
            # Right lane: positive slope, right half
            elif slope > 0.3 and x1 > w // 2:
                cv2.line(frame, (x1,y1), (x2,y2), (255, 100, 0), 2)
                right_detected = True

    return frame, left_detected, right_detected

def get_detections(frame):
    """
    Run YOLO and return list of detections for dashboard.
    Each detection: {label, confidence, bbox, danger}
    """
    detections = []
    results = model(frame, verbose=False)

    for result in results:
        for box in result.boxes:
            class_id   = int(box.cls[0])
            confidence = float(box.conf[0])
            threshold  = CONFIDENCE_THRESHOLDS.get(class_id, 0.45)

            if class_id not in TRAFFIC_CLASSES:
                continue
            if confidence < threshold:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label  = TRAFFIC_CLASSES[class_id]
            danger = DANGER_LEVEL[class_id]
            color  = DANGER_COLORS[danger]

            # Draw bounding box
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)

            # Label background for readability
            label_text = f"{label} {confidence:.2f}"
            (tw, th), _ = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(frame,
                (x1, y1-th-8), (x1+tw+4, y1), color, -1)
            cv2.putText(frame, label_text,
                (x1+2, y1-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,0,0), 1)

            detections.append({
                "label":      label,
                "confidence": round(confidence, 2),
                "bbox":       [x1, y1, x2, y2],
                "danger":     danger,
            })

    return frame, detections

# ── Main loop ──
print("Traffic Detection — Victorian road rules")
print("Press Q to quit")

prev_time = time.time()
frame_count = 0
fps = 0

while True:
    frame = picam2.capture_array()
    frame = np.ascontiguousarray(frame[:, :, :3])  # fix Pi 5 memory layout

    # Lane detection
    frame, left_lane, right_lane = draw_lane_lines(frame)

    # YOLO detection
    frame, detections = get_detections(frame)

    # FPS counter (every 15 frames)
    frame_count += 1
    if frame_count % 15 == 0:
        curr_time = time.time()
        fps = round(15 / (curr_time - prev_time), 1)
        prev_time = curr_time

    # Overlay info
    cv2.putText(frame, f"FPS: {fps}",
        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.putText(frame,
        f"Lane L: {'OK' if left_lane else 'MISS'}  "
        f"R: {'OK' if right_lane else 'MISS'}",
        (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
        (0,255,0) if (left_lane and right_lane) else (0,165,255), 2)

    cv2.imshow("Traffic Detection — VIC", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

picam2.stop()
cv2.destroyAllWindows()