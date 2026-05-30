"""
instrument_cluster.py
─────────────────────
Runs as a Tkinter window directly on the Pi (via connect.raspberrypi)
No Flask/browser needed.
Combines:
  - camPLUSultra.py (Tkinter GUI, road graphic, ultrasonic, YOLO)
  - instrument_cluster dashboard design (3 circles, nav, indicators)
"""

import tkinter as tk
import time
import threading
import cv2
import numpy as np
from gpiozero import DistanceSensor
from picamera2 import Picamera2
from ultralytics import YOLO
try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("⚠️  PIL not found. Run: pip install pillow --break-system-packages")

# ── Constants ─────────────────────────────────────────────────
TRIGGER_PIN   = 5
ECHO_PIN      = 6
STOP_DISTANCE = 15
SLOW_DISTANCE = 40
MAX_RANGE_CM  = 400

W = 1400
H = 800

# ── Ultrasonic ────────────────────────────────────────────────
sensor = DistanceSensor(
    echo=ECHO_PIN, trigger=TRIGGER_PIN,
    max_distance=MAX_RANGE_CM / 100,
    queue_len=5, partial=True
)

def get_distance():
    try:
        d = sensor.distance
        return round(d * 100, 1) if d is not None else None
    except Exception:
        return None

# ── YOLO + Camera ─────────────────────────────────────────────
model = YOLO("yolov8n.pt")

TRAFFIC_CLASSES = {
    0:"person", 1:"bicycle", 2:"car", 3:"motorcycle",
    5:"bus", 6:"train", 7:"truck",
    9:"traffic light", 11:"stop sign",
}
DANGER_COLORS = {
    "high":   (0,0,255),
    "medium": (0,165,255),
    "low":    (0,255,255),
}
DANGER_LEVEL = {
    0:"high", 1:"medium", 2:"medium", 3:"medium",
    5:"medium", 6:"low", 7:"medium",
    9:"high", 11:"high",
}

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"format":"XRGB8888","size":(640,480)},
    controls={
        "FrameRate":60,"Sharpness":1.5,"Contrast":1.1,
        "Brightness":0.0,"AwbMode":0,"AeEnable":True,
        "NoiseReductionMode":1,
    },
    buffer_count=6
))
picam2.set_controls({"Sharpness":1.5})
picam2.start()
time.sleep(2)

# ── Shared state ──────────────────────────────────────────────
state = {
    "distance":        100,
    "zone":            "FAR",
    "status":          "FAST",
    "status_color":    "#30ff5a",
    "message":         "Path clear",
    "person":          False,
    "detections":      [],
    "forced_stop":     False,
    "stop_until":      0,
    "fps":             0,
    "speed":           0,        # 0-120 km/h (keyboard)
    "steer":           0,        # -90 to 90 degrees
    "gear":            "D",
    "braking":         True,
    "haz":             False,
    "ind_left":        False,
    "ind_right":       False,
    "road_offset":     0,
    "side_offset":     0,
    "frame_count":     0,
    "fps_timer":       time.time(),
    "moving":          False,
    "last_frame":      None,
    "auto_mode":       False,   # autonomous speed control
}

lock = threading.Lock()

# ── Camera thread ─────────────────────────────────────────────
def camera_thread():
    while True:
        raw   = picam2.capture_array()
        frame = np.ascontiguousarray(raw[:,:,:3])
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        results = model(frame, verbose=False)
        person  = False
        dets    = []

        for result in results:
            for box in result.boxes:
                cid  = int(box.cls[0])
                conf = float(box.conf[0])
                if cid not in TRAFFIC_CLASSES or conf < 0.45:
                    continue
                x1,y1,x2,y2 = map(int,box.xyxy[0])
                label  = TRAFFIC_CLASSES[cid]
                danger = DANGER_LEVEL.get(cid,"medium")
                color  = DANGER_COLORS[danger]
                if cid == 0: person = True
                cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)
                txt = f"{label} {conf:.2f}"
                (tw,th),_ = cv2.getTextSize(txt,cv2.FONT_HERSHEY_SIMPLEX,0.55,1)
                cv2.rectangle(frame,(x1,y1-th-8),(x1+tw+4,y1),color,-1)
                cv2.putText(frame,txt,(x1+2,y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,0,0),1)
                dets.append({"label":label,"danger":danger,"conf":round(conf,2)})

        # FPS
        with lock:
            state["frame_count"] += 1
            if state["frame_count"] % 15 == 0:
                now = time.time()
                state["fps"] = round(15/(now-state["fps_timer"]),1)
                state["fps_timer"] = now
            state["person"]     = person
            state["detections"] = dets
            state["last_frame"] = frame.copy()

threading.Thread(target=camera_thread, daemon=True).start()

# ── Tkinter GUI ───────────────────────────────────────────────
root = tk.Tk()
root.title("Instrument Cluster")
root.geometry(f"{W}x{H}")
root.configure(bg="#06111c")
root.resizable(False, False)

canvas = tk.Canvas(root, width=W, height=H, bg="#06111c", highlightthickness=0)
canvas.pack()

# Blinker animation state
blink_on = True

# Key tracking
keys_held = set()

def on_key_press(e):
    keys_held.add(e.keysym.lower())

def on_key_release(e):
    keys_held.discard(e.keysym.lower())
    # Reset steer when A/D/Left/Right released
    if e.keysym.lower() in ('a','d','left','right'):
        if 'a' not in keys_held and 'left' not in keys_held and \
           'd' not in keys_held and 'right' not in keys_held:
            pass  # handled in update loop

root.bind('<KeyPress>',   on_key_press)
root.bind('<KeyRelease>', on_key_release)
root.focus_set()

# ── Drawing helpers ───────────────────────────────────────────
def draw_circle_panel(cx, cy, r, title=""):
    """Draw 3D-style circle panel."""
    # Outer bezel
    canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                       fill="#1e1e1e", outline="#3a3a3a", width=3)
    # Inner ring
    r2 = int(r*0.92)
    canvas.create_oval(cx-r2, cy-r2, cx+r2, cy+r2,
                       fill="#111111", outline="#222222", width=2)
    # Inner bowl
    r3 = int(r*0.82)
    canvas.create_oval(cx-r3, cy-r3, cx+r3, cy+r3,
                       fill="#0d0d0d", outline="#1a1a1a", width=1)
    # Highlight
    canvas.create_oval(cx-r3+8, cy-r3+8, cx-r3+40, cy-r3+25,
                       fill="#ffffff", outline="", stipple="gray12")

def draw_arc_gauge(cx, cy, r, value, max_val, color):
    """Draw a circular arc gauge."""
    pct   = min(1.0, value / max_val)
    extent = pct * 270
    # Background arc
    canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                      start=135, extent=270,
                      style="arc", outline="#1a3a1a", width=10)
    if extent > 0:
        canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                          start=135, extent=extent,
                          style="arc", outline=color, width=10)

def draw_steer_arc(cx, cy, value):
    """Draw steering arc indicator."""
    # Background
    canvas.create_arc(cx-55, cy-30, cx+55, cy+80,
                      start=0, extent=180,
                      style="arc", outline="#222222", width=7)
    # Active arc
    t = (value + 90) / 180.0
    if value < 0:
        canvas.create_arc(cx-55, cy-30, cx+55, cy+80,
                          start=90, extent=int(-value * 0.9),
                          style="arc", outline="#3b82f6", width=7)
    elif value > 0:
        canvas.create_arc(cx-55, cy-30, cx+55, cy+80,
                          start=90, extent=-int(value * 0.9),
                          style="arc", outline="#3b82f6", width=7)
    # Dot position on arc
    import math
    angle_deg = 180 - t * 180
    angle_rad = math.radians(angle_deg)
    dx = int(55 * math.cos(angle_rad))
    dy = int(-30 * math.sin(angle_rad)) + 25
    canvas.create_oval(cx+dx-6, cy+dy-6, cx+dx+6, cy+dy+6,
                       fill="#3b82f6", outline="")

def draw_tree(x, y, scale):
    canvas.create_rectangle(x-8*scale, y, x+8*scale, y+50*scale,
                            fill="#4b2e16", outline="")
    canvas.create_oval(x-35*scale, y-35*scale, x+35*scale, y+35*scale,
                       fill="#14532d", outline="#22c55e", width=1)

def draw_road_graphic(cx, cy, w, h, road_off, side_off, steer, braking, moving):
    """Draw the road + car + turning path in a bounding box."""
    # Road background
    canvas.create_rectangle(cx, cy, cx+w, cy+h,
                            fill="#06111c", outline="#1e3a4f", width=1)

    # 3-lane road
    pts = [cx+w*0.18,cy+h, cx+w*0.38,cy+h*0.3,
           cx+w*0.62,cy+h*0.3, cx+w*0.82,cy+h]
    canvas.create_polygon(*pts, fill="#132433", outline="#dbeafe", width=2)

    # Lane dividers (dashed)
    for lane_x_top, lane_x_bot in [(0.46,0.31),(0.54,0.69)]:
        for i in range(8):
            y1 = cy + h*0.3 + ((i*0.09 + road_off/float(h))*h*0.7) % (h*0.7)
            y2 = min(cy+h, y1 + h*0.05)
            t1 = (y1 - (cy+h*0.3))/(h*0.7)
            t2 = (y2 - (cy+h*0.3))/(h*0.7)
            x1 = cx + w*(lane_x_top*(1-t1) + lane_x_bot*t1)
            x2 = cx + w*(lane_x_top*(1-t2) + lane_x_bot*t2)
            canvas.create_line(x1,y1,x2,y2, fill="white", width=1)

    # Trees
    for i in range(5):
        sy = cy+h*0.3 + ((i*0.18+side_off/float(h))*h*0.7) % (h*0.7)
        sc = max(0.3, (sy-(cy+h*0.3))/(h*0.7))
        draw_tree(int(cx+w*0.1-20*sc), int(sy), sc)
        draw_tree(int(cx+w*0.9+20*sc), int(sy), sc)

    # Turning path
    car_x = cx + w*0.5
    car_y = cy + h*0.78
    path_color = "#f0a500" if abs(steer) >= 20 else "#2ecc40"
    if steer <= -20:
        canvas.create_line(car_x, car_y-10,
                           car_x-30, car_y-60,
                           car_x-80, car_y-120,
                           smooth=True, fill=path_color,
                           width=2, dash=(6,5))
    elif steer >= 20:
        canvas.create_line(car_x, car_y-10,
                           car_x+30, car_y-60,
                           car_x+80, car_y-120,
                           smooth=True, fill=path_color,
                           width=2, dash=(6,5))
    else:
        canvas.create_line(car_x, car_y-10,
                           car_x, car_y-120,
                           fill=path_color, width=2, dash=(6,5))

    # Car body (top view)
    cw, ch = 28, 52
    bx, by = int(car_x - cw//2), int(car_y - ch//2)
    canvas.create_rectangle(bx, by, bx+cw, by+ch,
                            fill="#cc2200", outline="#ff4400", width=1)
    # Windscreen
    canvas.create_rectangle(bx+3, by+5, bx+cw-3, by+16,
                            fill="#0d0800", outline="#38bdf8", width=1)
    # Rear window
    canvas.create_rectangle(bx+3, by+ch-16, bx+cw-3, by+ch-5,
                            fill="#0d0800", outline="", width=0)
    # Wheels
    for wx, wy in [(bx-4,by+6),(bx+cw,by+6),(bx-4,by+ch-16),(bx+cw,by+ch-16)]:
        canvas.create_rectangle(wx, wy, wx+5, wy+10, fill="#111", outline="")
    # Headlights
    canvas.create_rectangle(bx+3, by, bx+10, by+3, fill="#ffe066", outline="")
    canvas.create_rectangle(bx+cw-10, by, bx+cw-3, by+3, fill="#ffe066", outline="")
    # Taillights
    tl_color = "#ff0000" if braking else "#880000"
    canvas.create_rectangle(bx+3, by+ch-3, bx+10, by+ch, fill=tl_color, outline="")
    canvas.create_rectangle(bx+cw-10, by+ch-3, bx+cw-3, by+ch, fill=tl_color, outline="")

def zone_pill_color(zone):
    return {"CRITICAL":"#e74c3c","NEAR":"#f0a500","MID":"#4a9eff",
            "FAR":"#2ecc40","CLEAR":"#555"}.get(zone,"#2ecc40")

# ── Main update loop ──────────────────────────────────────────
ACCEL   = 2
DECEL   = 3
BRAKE   = 6
STEER_R = 3
STEER_C = 2

def update():
    global blink_on
    now = time.time()

    # ── Key handling ──
    spd   = state["speed"]
    steer = state["steer"]
    gear  = state["gear"]
    prev_spd = spd

    if ('w' in keys_held or 'up' in keys_held) and gear == 'D':
        spd = min(120, spd + ACCEL)
    if 's' in keys_held or 'down' in keys_held:
        spd = max(0, spd - DECEL)
    if ' ' in keys_held:
        spd = max(0, spd - BRAKE)
    if 'a' in keys_held or 'left' in keys_held:
        steer = max(-90, steer - STEER_R)
    elif 'd' in keys_held or 'right' in keys_held:
        steer = min(90, steer + STEER_R)
    else:
        # Auto-return to centre
        if steer < 0: steer = min(0, steer + STEER_C)
        if steer > 0: steer = max(0, steer - STEER_C)

    # Braking logic
    braking = state["braking"]
    if spd == 0:
        braking = True
    elif spd < prev_spd:
        braking = True
    elif spd > prev_spd and gear == 'D':
        braking = False

    moving = ('w' in keys_held or 'up' in keys_held) and gear == 'D' and spd > 0

    # Road animation
    road_off = state["road_offset"]
    side_off = state["side_offset"]
    if moving:
        step = 18 if spd > 80 else 10 if spd > 40 else 5
        road_off = (road_off + step) % 1000
        side_off = (side_off + int(step*1.4)) % 1000

    # Indicators
    haz      = state["haz"]
    ind_left  = state["ind_left"]
    ind_right = state["ind_right"]
    show_l = haz or ind_left  or (steer <= -20 and not ind_right and not haz)
    show_r = haz or ind_right or (steer >=  20 and not ind_left  and not haz)
    blink_on = not blink_on

    # Ultrasonic
    dist = get_distance()
    if dist is None: dist = state["distance"]
    if dist < STOP_DISTANCE and now >= state["stop_until"]:
        state["stop_until"] = now + 3
    forced = now < state["stop_until"]

    zone = ("CRITICAL" if dist<=20 else "NEAR" if dist<=50
            else "MID" if dist<=150 else "FAR" if dist<=300 else "CLEAR")

    person = state["person"]
    dets   = state["detections"]

    if forced or (person and dist < STOP_DISTANCE) or dist < STOP_DISTANCE:
        st_color, st_text, st_msg = "#ff3b30", "STOP", "Obstacle detected"
        # Smooth emergency stop — ramp down fast but not instant
        spd = max(0, spd - BRAKE)
        braking = True
    elif dist < SLOW_DISTANCE or (person and dist < SLOW_DISTANCE):
        st_color, st_text, st_msg = "#ffd60a", "SLOW", "Object nearby"
    else:
        st_color, st_text, st_msg = "#30ff5a", "FAST", "Path clear"

    # Autonomous mode — smooth speed control based on zone
    auto_mode = state["auto_mode"]
    if auto_mode and gear == "D":
        # Target speed per zone
        if forced or zone == "CRITICAL":
            target = 0
        elif zone == "NEAR":
            target = 40
        elif zone == "MID":
            target = 60
        elif zone == "FAR":
            target = 80
        else:  # CLEAR
            target = 100

        # Smooth transition — ramp up or down gradually
        if spd < target:
            spd = min(target, spd + ACCEL)       # accelerate smoothly
        elif spd > target:
            spd = max(target, spd - DECEL)       # decelerate smoothly
        braking = spd < state["speed"]           # braking if slowing down

    # Save state
    state.update({
        "speed":        spd,
        "steer":        steer,
        "braking":      braking,
        "moving":       moving,
        "distance":     dist,
        "zone":         zone,
        "road_offset":  road_off,
        "side_offset":  side_off,
    })

    fps_val = state["fps"]

    # ── Draw everything ───────────────────────────────────────
    canvas.delete("all")
    canvas.create_rectangle(0,0,W,H, fill="#08080a", outline="")

    # Speed gauge colour
    spd_color = "#e74c3c" if spd>80 else "#f0a500" if spd>50 else "#2ecc40"

    # ── LEFT CIRCLE — Speed + Gear + Nav ─────────────────────
    lcx, lcy, lr = 210, 400, 185
    draw_circle_panel(lcx, lcy, lr)
    draw_arc_gauge(lcx, lcy, 155, spd, 120, spd_color)

    # Speed number
    canvas.create_text(lcx, lcy-30, text=str(int(spd)),
                       fill="white", font=("Arial",54,"bold"))
    canvas.create_text(lcx, lcy+28, text="km/h",
                       fill="#555", font=("Arial",12))

    # Gear selector
    gears = ["P","R","N","D"]
    gx = lcx - 60
    for g in gears:
        color = "white" if g == gear else "#222"
        size  = 16 if g == gear else 13
        canvas.create_text(gx, lcy+60, text=g, fill=color,
                           font=("Arial",size,"bold"))
        gx += 40

    # Divider
    canvas.create_line(lcx-100, lcy+80, lcx+100, lcy+80, fill="#1c1c1c", width=1)

    # Nav segments
    canvas.create_text(lcx, lcy+93, text="NAVIGATION", fill="#333", font=("Arial",9))
    seg_x = lcx - 62
    for stype, sw in [("str",16),("str",16),("cur",13),("cur",13),("str",11)]:
        col = "#2ecc40" if stype=="str" else "#f0a500"
        canvas.create_rectangle(seg_x, lcy+104, seg_x+sw, lcy+110, fill=col, outline="")
        seg_x += sw + 4
    canvas.create_text(lcx, lcy+122, text="Curve ahead · 120m",
                       fill="#444", font=("Arial",10))

    # Divider
    canvas.create_line(lcx-100, lcy+134, lcx+100, lcy+134, fill="#1c1c1c", width=1)

    # Path status
    canvas.create_text(lcx, lcy+146, text="PATH STATUS", fill="#333", font=("Arial",9))
    if dets:
        high = next((d for d in dets if d["danger"]=="high"), dets[0])
        ps_text  = f"⛔ {high['label']}" if high["danger"]=="high" else f"⚠ {high['label']}"
        ps_color = "#e74c3c" if high["danger"]=="high" else "#f0a500"
    else:
        ps_text  = "● " + st_msg
        ps_color = st_color
    canvas.create_text(lcx, lcy+163, text=ps_text,
                       fill=ps_color, font=("Arial",13,"bold"))

    # Auto mode indicator
    am_color = "#2ecc40" if auto_mode else "#333"
    am_text  = "AUTO: ON" if auto_mode else "AUTO: OFF"
    canvas.create_text(lcx, lcy+182, text=am_text,
                       fill=am_color, font=("Arial",10,"bold"))

    # ── MIDDLE — Road graphic + Camera ────────────────────────
    mx, my, mw, mh = 430, 60, 540, 680

    # Road graphic (top half of middle)
    draw_road_graphic(mx, my, mw, int(mh*0.42),
                      road_off, side_off, steer, braking, moving)

    # Camera feed (bottom half of middle)
    cam_y = my + int(mh*0.44)
    cam_h = int(mh*0.56)
    canvas.create_rectangle(mx, cam_y, mx+mw, cam_y+cam_h,
                            fill="#000", outline="#1e3a4f", width=1)

    frame = state.get("last_frame")
    if frame is not None and PIL_OK:
        try:
            frame_rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (mw, cam_h))
            img = ImageTk.PhotoImage(Image.fromarray(frame_resized))
            canvas._cam_img = img   # must keep reference or GC kills it
            canvas.create_image(mx, cam_y, anchor="nw", image=img)
        except Exception as e:
            canvas.create_text(mx+mw//2, cam_y+cam_h//2,
                              text=f"Camera error: {e}",
                              fill="#e74c3c", font=("Arial",10))
    elif not PIL_OK:
        canvas.create_text(mx+mw//2, cam_y+cam_h//2,
                          text="Install: pip install pillow",
                          fill="#e74c3c", font=("Arial",11))
    else:
        canvas.create_text(mx+mw//2, cam_y+cam_h//2,
                          text="Camera loading...",
                          fill="#555", font=("Arial",12))

    # YOLO LIVE label + FPS
    canvas.create_text(mx+10, cam_y+15,
                       text=f"● YOLO · LIVE   FPS:{fps_val}",
                       fill="#2ecc40", font=("Arial",10), anchor="w")

    # Detection pills
    pill_x = mx + 8
    for det in dets[:4]:
        dc = "#e74c3c" if det["danger"]=="high" else \
             "#f0a500" if det["danger"]=="medium" else "#f0f000"
        txt = f"{det['label']} {int(det['conf']*100)}%"
        canvas.create_rectangle(pill_x, cam_y+cam_h-24,
                                pill_x+len(txt)*7+8, cam_y+cam_h-6,
                                fill="#0d0d0d", outline=dc, width=1)
        canvas.create_text(pill_x+4, cam_y+cam_h-15, text=txt,
                           fill=dc, font=("Arial",9), anchor="w")
        pill_x += len(txt)*7 + 16

    # ── RIGHT CIRCLE — Ultrasonic + Steering + Braking ───────
    rcx, rcy, rr = 1190, 400, 185
    draw_circle_panel(rcx, rcy, rr)

    # Ultrasonic
    canvas.create_text(rcx, rcy-130, text="ULTRASONIC",
                       fill="#444", font=("Arial",9))
    dist_color = zone_pill_color(zone)
    canvas.create_text(rcx, rcy-100, text=f"{dist:.0f}",
                       fill="white", font=("Arial",32,"bold"))
    canvas.create_text(rcx+38, rcy-96, text="cm",
                       fill="#444", font=("Arial",12))
    canvas.create_text(rcx, rcy-72, text=zone,
                       fill=dist_color, font=("Arial",12,"bold"))
    # Distance bar
    bar_w = 120
    bar_pct = min(1.0, dist/400)
    canvas.create_rectangle(rcx-bar_w//2, rcy-58,
                            rcx+bar_w//2, rcy-50,
                            fill="#1a1a1a", outline="")
    canvas.create_rectangle(rcx-bar_w//2, rcy-58,
                            rcx-bar_w//2+int(bar_w*bar_pct), rcy-50,
                            fill=dist_color, outline="")

    # Divider
    canvas.create_line(rcx-80, rcy-38, rcx+80, rcy-38, fill="#222", width=1)

    # Steering angle
    canvas.create_text(rcx, rcy-22, text="STEERING ANGLE",
                       fill="#444", font=("Arial",9))
    draw_steer_arc(rcx, rcy-10, steer)
    canvas.create_text(rcx, rcy+50, text=f"{abs(steer)}°",
                       fill="#3b82f6", font=("Arial",20,"bold"))
    steer_dir = "Left" if steer<-5 else "Right" if steer>5 else "Centre"
    canvas.create_text(rcx, rcy+72, text=steer_dir,
                       fill="#555", font=("Arial",11))

    # Divider
    canvas.create_line(rcx-80, rcy+88, rcx+80, rcy+88, fill="#222", width=1)

    # Braking
    canvas.create_text(rcx, rcy+102, text="BRAKING",
                       fill="#444", font=("Arial",9))
    brak_text  = "ACTIVE" if braking else "OFF"
    brak_color = "#e74c3c" if braking else "#555"
    canvas.create_text(rcx, rcy+126, text=brak_text,
                       fill=brak_color, font=("Arial",18,"bold"))

    # ── TOP BAR — Clock + Indicators + Day/Night ─────────────
    canvas.create_rectangle(0,0,W,50, fill="#0a0a0a", outline="#1c1c1c")

    # Clock
    import datetime
    clk = datetime.datetime.now().strftime("%H:%M")
    canvas.create_text(80, 25, text=clk, fill="white", font=("Arial",22,"bold"))
    canvas.create_text(175, 25, text="Melbourne · 24°C",
                       fill="#444", font=("Arial",11))

    # Indicators — centre of top bar
    l_color = "#2ecc40" if (show_l and blink_on) else "#1a2e1a"
    r_color = "#2ecc40" if (show_r and blink_on) else "#1a2e1a"
    h_color = "#f0a500" if (haz and blink_on) else "#2a1e00"

    canvas.create_text(W//2-80, 25, text="◄",
                       fill=l_color, font=("Arial",26,"bold"))
    canvas.create_rectangle(W//2-55, 10, W//2+55, 40,
                            fill="#111", outline="#333", width=1)
    canvas.create_text(W//2, 25, text="⚠ HAZARD",
                       fill=h_color, font=("Arial",12,"bold"))
    canvas.create_text(W//2+80, 25, text="►",
                       fill=r_color, font=("Arial",26,"bold"))

    # Status bar bottom
    canvas.create_rectangle(0,H-45,W,H, fill="#0a0a0a", outline="#1c1c1c")
    if auto_mode:
        zone_speeds = {"CRITICAL":0,"NEAR":40,"MID":60,"FAR":80,"CLEAR":100}
        tgt = zone_speeds.get(zone, 60)
        auto_label = f"  [AUTO → {tgt} km/h]"
    else:
        auto_label = ""
    canvas.create_text(100, H-22, text=f"Status: {st_text}{auto_label}",
                       fill=st_color, font=("Arial",13,"bold"), anchor="w")
    canvas.create_text(350, H-22, text=f"Distance: {dist:.0f}cm | Zone: {zone}",
                       fill="#555", font=("Arial",11), anchor="w")
    canvas.create_text(750, H-22, text=f"Steer: {steer}°  Speed: {spd} km/h  Gear: {gear}",
                       fill="#555", font=("Arial",11), anchor="w")

    root.after(100, update)  # 10Hz GUI refresh

# ── Key bindings for gear + hazard ───────────────────────────
def toggle_haz(e=None):
    state["haz"] = not state["haz"]
    state["ind_left"] = False
    state["ind_right"] = False

def toggle_ind_left(e=None):
    if state["haz"]: return
    state["ind_left"]  = not state["ind_left"]
    state["ind_right"] = False

def toggle_ind_right(e=None):
    if state["haz"]: return
    state["ind_right"] = not state["ind_right"]
    state["ind_left"]  = False

def set_gear(g):
    state["gear"] = g
    if g in ("P","N"):
        state["speed"] = 0

def toggle_auto(e=None):
    state["auto_mode"] = not state["auto_mode"]
    if state["auto_mode"]:
        state["gear"] = "D"

root.bind('h', toggle_haz)
root.bind('m', toggle_auto)
root.bind('z', toggle_ind_left)
root.bind('x', toggle_ind_right)
root.bind('p', lambda e: set_gear('P'))
root.bind('n', lambda e: set_gear('N'))
root.bind('r', lambda e: set_gear('R'))
root.bind('g', lambda e: set_gear('D'))



# ── Cleanup + run ─────────────────────────────────────────────
def on_close():
    picam2.stop()
    cv2.destroyAllWindows()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

update()
root.mainloop()
