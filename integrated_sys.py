"""
instrument_cluster.py
─────────────────────
Autonomous Vehicle Dashboard — Complete Final Version
Integrates:
  - Ultrasonic sensor (GPIO5/GPIO6)
  - Raspberry Pi Camera (Waveshare IR-Cut, hiRES config)
  - YOLOv8n object detection (Victorian road rules)
  - Lane detection (Hough transform)
  - Flask web server → templates/instrument_cluster.html

Run modes:
  python instrument_cluster.py                         → Pi camera + ultrasonic
  python instrument_cluster.py --video                 → prompts for video path
  python instrument_cluster.py --video test.mp4        → direct video path

Access dashboard:
  http://localhost:5000        (on Pi)
  http://<Pi-IP>:5000          (from laptop on same WiFi/hotspot)
"""

import argparse
import threading
import time
import cv2
import numpy as np
from flask import Flask, render_template, jsonify, Response

# ── Argument parser ───────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument(
    "--video", nargs="?", const="prompt",
    help="Use a video file instead of Pi camera."
)
args = parser.parse_args()
USE_VIDEO = args.video is not None

if USE_VIDEO:
    if args.video == "prompt" or args.video is None:
        VIDEO_PATH = input("Enter video file path: ").strip()
    else:
        VIDEO_PATH = args.video
    print(f"Video mode: {VIDEO_PATH}")
else:
    print("Pi camera mode")

# ── Ultrasonic sensor ─────────────────────────────────────────
try:
    from gpiozero import DistanceSensor

    TRIGGER_PIN  = 5
    ECHO_PIN     = 6
    STOP_DIST    = 15    # cm — stop immediately
    SLOW_DIST    = 40    # cm — slow down

    sensor = DistanceSensor(
        echo=ECHO_PIN,
        trigger=TRIGGER_PIN,
        max_distance=4.0,   # 400cm in metres
        queue_len=5,
        partial=True
    )

    def get_distance():
        try:
            d = sensor.distance
            return round(d * 100, 1) if d is not None else None
        except Exception:
            return None

    ULTRASONIC_OK = True
    print("✅ Ultrasonic sensor loaded (GPIO5/GPIO6)")

except Exception as e:
    ULTRASONIC_OK = False
    print(f"⚠️  Ultrasonic not available ({e}) — simulating distance")
    import random
    def get_distance():
        return random.randint(80, 400)

# ── YOLO model ────────────────────────────────────────────────
from ultralytics import YOLO
model = YOLO("yolov8n.pt")
print("✅ YOLO model loaded")

# Victorian road rule relevant classes
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

DANGER_LEVEL = {
    0:  "high",    # person — highest priority
    1:  "medium",  # bicycle
    2:  "medium",  # car
    3:  "medium",  # motorcycle
    5:  "medium",  # bus
    6:  "low",     # train
    7:  "medium",  # truck
    9:  "high",    # traffic light
    11: "high",    # stop sign
    12: "low",     # parking meter
}

# BGR colours per danger level
DANGER_COLORS = {
    "high":   (0, 0, 255),     # red
    "medium": (0, 165, 255),   # orange
    "low":    (0, 255, 255),   # yellow
}

# Per-class confidence thresholds
CONF_THRESH = {
    0:  0.50,   # person
    1:  0.45,   # bicycle
    2:  0.45,   # car
    3:  0.45,   # motorcycle
    5:  0.45,   # bus
    6:  0.40,   # train
    7:  0.45,   # truck
    9:  0.40,   # traffic light
    11: 0.40,   # stop sign
    12: 0.40,   # parking meter
}

# ── Shared sensor state ───────────────────────────────────────
sensor_data = {
    "distance_cm":        400,
    "zone":               "FAR",
    "path_status":        "No obstacles",
    "path_status_color":  "#2ecc40",
    "left_lane":          False,
    "right_lane":         False,
    "detections":         [],       # list of {label, confidence, danger}
    "person_detected":    False,
    "speed_status":       "FAST",
    "speed_status_color": "#30ff5a",
    "moving":             False,    # controlled by W/↑ key from dashboard
}

# Latest JPEG frame for /video stream
latest_frame = None
frame_lock    = threading.Lock()

# Forced stop timer (3 seconds when obstacle critical)
stop_until  = 0
last_dist   = 100

# ── Helper functions ──────────────────────────────────────────
def zone_from_dist(d):
    """Classify distance into zones."""
    if d <= 20:    return "CRITICAL"
    elif d <= 50:  return "NEAR"
    elif d <= 150: return "MID"
    elif d <= 300: return "FAR"
    else:          return "OUT_OF_RANGE"

def path_from_zone(zone):
    """Return (status_text, colour) for a given zone."""
    return {
        "CRITICAL":     ("Obstacle critical", "#e74c3c"),
        "NEAR":         ("Obstacle nearby",   "#f0a500"),
        "MID":          ("Monitoring",        "#4a9eff"),
        "FAR":          ("No obstacles",      "#2ecc40"),
        "OUT_OF_RANGE": ("Out of range",      "#555555"),
    }.get(zone, ("No obstacles", "#2ecc40"))

def speed_from_dist(d, person_detected, forced_stop):
    """Return (speed_status, colour) based on distance and detection."""
    if forced_stop:
        return "STOP", "#ff3b30"
    if person_detected and d < STOP_DIST:
        return "STOP", "#ff3b30"
    if d < STOP_DIST:
        return "STOP", "#ff3b30"
    if d < SLOW_DIST:
        return "SLOW", "#ffd60a"
    return "FAST", "#30ff5a"

def draw_lane_lines(frame):
    """
    Detect lane lines using Hough transform.
    Returns frame with lines drawn + (left_detected, right_detected).
    """
    h, w = frame.shape[:2]
    roi_top = int(h * 0.55)

    gray   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur   = cv2.GaussianBlur(gray, (5, 5), 0)
    edges  = cv2.Canny(blur, 50, 150)

    mask   = np.zeros_like(edges)
    roi    = np.array([[
        (int(w*0.05), h),
        (int(w*0.45), roi_top),
        (int(w*0.55), roi_top),
        (int(w*0.95), h)
    ]], dtype=np.int32)
    cv2.fillPoly(mask, roi, 255)
    masked = cv2.bitwise_and(edges, mask)

    lines  = cv2.HoughLinesP(
        masked, 1, np.pi/180,
        threshold=30, minLineLength=40, maxLineGap=80
    )

    left = right = False
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 == x1:
                continue
            slope = (y2 - y1) / (x2 - x1)
            if slope < -0.3 and x1 < w // 2:
                cv2.line(frame, (x1,y1), (x2,y2), (255,100,0), 2)
                left = True
            elif slope > 0.3 and x1 > w // 2:
                cv2.line(frame, (x1,y1), (x2,y2), (255,100,0), 2)
                right = True

    return frame, left, right

def run_yolo(frame):
    """
    Run YOLO detection on frame.
    Returns frame with boxes drawn, list of detections, person_detected flag.
    """
    detections      = []
    person_detected = False

    results = model(frame, verbose=False)
    for result in results:
        for box in result.boxes:
            class_id   = int(box.cls[0])
            confidence = float(box.conf[0])
            threshold  = CONF_THRESH.get(class_id, 0.45)

            if class_id not in TRAFFIC_CLASSES:
                continue
            if confidence < threshold:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label  = TRAFFIC_CLASSES[class_id]
            danger = DANGER_LEVEL[class_id]
            color  = DANGER_COLORS[danger]

            if class_id == 0:
                person_detected = True

            # Draw bounding box
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)

            # Label with solid background for readability
            label_text = f"{label} {confidence:.2f}"
            (tw, th), _ = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(frame, (x1, y1-th-8), (x1+tw+4, y1), color, -1)
            cv2.putText(frame, label_text, (x1+2, y1-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,0,0), 1)

            detections.append({
                "label":      label,
                "confidence": round(confidence, 2),
                "danger":     danger,
            })

    return frame, detections, person_detected

# ── Ultrasonic thread ─────────────────────────────────────────
def ultrasonic_loop():
    """Continuously reads ultrasonic sensor and updates sensor_data."""
    global stop_until, last_dist

    while True:
        d   = get_distance()
        now = time.time()

        # Fall back to last known distance on sensor glitch
        if d is None:
            d = last_dist
        else:
            last_dist = d

        # Forced 3-second stop when object is critical
        if d < STOP_DIST and now >= stop_until:
            stop_until = now + 3
        forced = now < stop_until

        zone   = zone_from_dist(d)
        status, color = path_from_zone(zone)
        spd_status, spd_color = speed_from_dist(
            d, sensor_data.get("person_detected", False), forced)

        sensor_data["distance_cm"]        = d
        sensor_data["zone"]               = zone
        sensor_data["path_status"]        = status
        sensor_data["path_status_color"]  = color
        sensor_data["speed_status"]       = spd_status
        sensor_data["speed_status_color"] = spd_color

        time.sleep(0.06)   # ~16Hz update rate

# ── Camera / video thread ─────────────────────────────────────
def camera_loop():
    """Captures frames, runs YOLO + lane detection, encodes JPEG for stream."""
    global latest_frame

    if USE_VIDEO:
        # ── Video file mode (Windows/laptop testing) ──
        cap = cv2.VideoCapture(VIDEO_PATH)
        if not cap.isOpened():
            print(f"❌ ERROR: Cannot open video: {VIDEO_PATH}")
            return

        fps   = cap.get(cv2.CAP_PROP_FPS) or 30
        delay = 1.0 / fps
        print(f"✅ Video loaded — {fps:.0f} fps")

        while True:
            ret, frame = cap.read()
            if not ret:
                # Loop video back to start
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = cv2.resize(frame, (640, 480))
            frame, left, right    = draw_lane_lines(frame)
            frame, dets, person   = run_yolo(frame)

            sensor_data["left_lane"]      = left
            sensor_data["right_lane"]     = right
            sensor_data["detections"]     = dets
            sensor_data["person_detected"]= person

            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
            with frame_lock:
                latest_frame = jpeg.tobytes()

            time.sleep(delay)

        cap.release()

    else:
        # ── Pi camera mode ──
        try:
            from picamera2 import Picamera2
        except ImportError:
            print("❌ ERROR: picamera2 not available.")
            print("   On Windows use: python instrument_cluster.py --video path/to/video.mp4")
            return

        picam2 = Picamera2()
        picam2.configure(
            picam2.create_video_configuration(
                main={"format": "XRGB8888", "size": (640, 480)},
                controls={
                    "FrameRate":         60,    # push FPS — YOLO limits actual rate
                    "Sharpness":         1.5,
                    "Contrast":          1.1,
                    "Brightness":        0.0,
                    "AwbMode":           0,     # auto white balance
                    "AeEnable":          True,  # auto exposure
                    "NoiseReductionMode":1,     # fast mode — less CPU
                },
                buffer_count=6
            )
        )
        picam2.set_controls({"Sharpness": 1.5})
        picam2.start()
        time.sleep(2)   # warm up camera + AWB
        print("✅ Pi camera started")

        while True:
            raw   = picam2.capture_array()
            # Fix Pi 5 memory layout + drop X channel from XRGB8888
            frame = np.ascontiguousarray(raw[:, :, :3])
            # Rotate 180° (Waveshare IR-Cut camera mounted inverted)
            frame = cv2.rotate(frame, cv2.ROTATE_180)

            frame, left, right    = draw_lane_lines(frame)
            frame, dets, person   = run_yolo(frame)

            sensor_data["left_lane"]       = left
            sensor_data["right_lane"]      = right
            sensor_data["detections"]      = dets
            sensor_data["person_detected"] = person

            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
            with frame_lock:
                latest_frame = jpeg.tobytes()

# ── Flask app ─────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/")
def index():
    """Serve the dashboard HTML."""
    return render_template("instrument_cluster.html")

@app.route("/data")
def data():
    """
    Returns live sensor + detection data as JSON.
    Dashboard polls this every 500ms.
    """
    return jsonify(sensor_data)

@app.route("/set_moving/<int:val>")
def set_moving(val):
    """
    Called by dashboard when W/↑ is held or released.
    Controls road animation speed.
    """
    sensor_data["moving"] = bool(val)
    return "ok"

@app.route("/video")
def video():
    """
    MJPEG stream endpoint.
    Dashboard <img src='/video'> connects here for live camera feed.
    """
    def generate():
        while True:
            with frame_lock:
                frame = latest_frame
            if frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame +
                    b"\r\n"
                )
            time.sleep(0.033)   # ~30fps stream

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

# ── Start background threads ──────────────────────────────────
threading.Thread(target=ultrasonic_loop, daemon=True).start()
threading.Thread(target=camera_loop,     daemon=True).start()

# ── Run Flask ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 40)
    print("  Dashboard running!")
    print("  http://localhost:5000        (on Pi)")
    print("  http://<Pi-IP>:5000          (from laptop)")
    print("=" * 40)
    app.run(host="0.0.0.0", port=5000, debug=False)