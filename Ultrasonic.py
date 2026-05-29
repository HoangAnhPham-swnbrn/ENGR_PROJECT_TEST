from gpiozero import DistanceSensor
from time import sleep

TRIGGER_PIN = 5   # BCM GPIO5 = BOARD Pin 29
ECHO_PIN = 6      # BCM GPIO6 = BOARD Pin 31

MAX_RANGE_CM = 400
SAMPLE_SIZE = 5
SAMPLE_WAIT = 0.06

ZONE_CRITICAL = 20
ZONE_NEAR     = 50
ZONE_MID      = 150
ZONE_FAR      = 300

sensor = DistanceSensor(
    echo=ECHO_PIN,
    trigger=TRIGGER_PIN,
    max_distance=MAX_RANGE_CM / 100,
    queue_len=SAMPLE_SIZE,
    partial=True
)

def get_zone(distance_cm):
    if distance_cm is None:
        return "UNKNOWN"
    elif distance_cm <= ZONE_CRITICAL:
        return "CRITICAL"
    elif distance_cm <= ZONE_NEAR:
        return "NEAR"
    elif distance_cm <= ZONE_MID:
        return "MID"
    elif distance_cm <= ZONE_FAR:
        return "FAR"
    else:
        return "OUT_OF_RANGE"

def get_distance():
    try:
        d = sensor.distance
        if d is None:
            return None
        return d * 100
    except Exception:
        return None

if __name__ == "__main__":
    print("Ultrasonic sensor running. Ctrl+C to stop.")
    print(f"Zones: CRITICAL<{ZONE_CRITICAL}cm | NEAR<{ZONE_NEAR}cm | "
          f"MID<{ZONE_MID}cm | FAR<{ZONE_FAR}cm")

    while True:
        distance = get_distance()
        zone = get_zone(distance)

        if distance is None:
            print("Sensor error — check wiring")
        else:
            print(f"Distance: {distance:.1f} cm  |  Zone: {zone}")

        sleep(SAMPLE_WAIT)
