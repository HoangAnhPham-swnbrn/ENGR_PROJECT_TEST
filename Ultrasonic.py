from gpiozero import DistanceSensor
from time import sleep
import collections

# ── Pin config ────────────────────────────────────────────────
TRIGGER_PIN = 5
ECHO_PIN    = 6

# ── Range config ──────────────────────────────────────────────
MAX_RANGE_CM  = 400
MIN_VALID_CM  = 3      # anything below this is electrical noise — ignore
SAMPLE_SIZE   = 5      # rolling average window
SAMPLE_WAIT   = 0.06   # min 0.06s between readings for HC-SR04

# ── Zone thresholds (cm) ──────────────────────────────────────
ZONE_CRITICAL = 20
ZONE_NEAR     = 50
ZONE_MID      = 150
ZONE_FAR      = 300

# ── Noise rejection config ────────────────────────────────────
# How many consecutive valid readings needed before accepting a zone change
# Higher = more stable but slower to react
CONFIRM_COUNT = 3

# ── Sensor init ───────────────────────────────────────────────
sensor = DistanceSensor(
    echo=ECHO_PIN,
    trigger=TRIGGER_PIN,
    max_distance=MAX_RANGE_CM / 100,
    queue_len=SAMPLE_SIZE,
    partial=True
)

# ── State ─────────────────────────────────────────────────────
_last_valid    = None       # last accepted distance
_raw_history   = collections.deque(maxlen=8)   # raw reading buffer
_zone_buffer   = collections.deque(maxlen=CONFIRM_COUNT)  # zone confirmation

def _raw_distance():
    """Get raw distance from sensor in cm."""
    try:
        d = sensor.distance
        if d is None:
            return None
        return round(d * 100, 1)
    except Exception:
        return None

def get_distance():
    """
    Returns filtered, noise-rejected distance in cm.
    Filters out:
      - Readings below MIN_VALID_CM (electrical crosstalk)
      - Sudden spikes inconsistent with recent history
    Returns last valid reading if current read is bad.
    """
    global _last_valid

    raw = _raw_distance()

    # Reject None
    if raw is None:
        return _last_valid

    # Reject readings below minimum valid distance (noise floor)
    if raw < MIN_VALID_CM:
        return _last_valid

    # Spike rejection — if reading jumps more than 150cm from recent average,
    # and we have history, treat it as a spike and ignore
    if len(_raw_history) >= 3:
        recent_avg = sum(_raw_history) / len(_raw_history)
        if abs(raw - recent_avg) > 150:
            return _last_valid   # ignore spike

    # Reading passed all filters — accept it
    _raw_history.append(raw)
    _last_valid = raw
    return raw

def get_zone(distance_cm):
    """
    Classify distance into zones with confirmation filtering.
    A zone change only registers after CONFIRM_COUNT consecutive
    readings agree — prevents flickering between zones.
    """
    if distance_cm is None:
        return "UNKNOWN"

    # Raw zone from distance
    if distance_cm <= ZONE_CRITICAL:
        raw_zone = "CRITICAL"
    elif distance_cm <= ZONE_NEAR:
        raw_zone = "NEAR"
    elif distance_cm <= ZONE_MID:
        raw_zone = "MID"
    elif distance_cm <= ZONE_FAR:
        raw_zone = "FAR"
    else:
        raw_zone = "CLEAR"

    # Add to confirmation buffer
    _zone_buffer.append(raw_zone)

    # Only accept zone if all recent readings agree
    if len(_zone_buffer) == CONFIRM_COUNT and len(set(_zone_buffer)) == 1:
        return raw_zone
    elif len(_zone_buffer) > 0:
        # Return most common zone in buffer (majority vote)
        return max(set(_zone_buffer), key=list(_zone_buffer).count)
    return raw_zone

# ── Standalone test ───────────────────────────────────────────
if __name__ == "__main__":
    print("Ultrasonic sensor running. Ctrl+C to stop.")
    print(f"Noise floor: ignore < {MIN_VALID_CM}cm")
    print(f"Zones: CRITICAL≤{ZONE_CRITICAL}cm | NEAR≤{ZONE_NEAR}cm | "
          f"MID≤{ZONE_MID}cm | FAR≤{ZONE_FAR}cm | CLEAR>{ZONE_FAR}cm")
    print("-" * 50)

    while True:
        distance = get_distance()
        zone     = get_zone(distance)

        if distance is None:
            print("Sensor error — check wiring")
        else:
            bar = "█" * int(min(distance, 400) / 10)
            print(f"Distance: {distance:6.1f} cm  |  Zone: {zone:<10}  |  {bar}")

        sleep(SAMPLE_WAIT)
