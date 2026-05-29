import time
from gpiozero import Servo

SERVO_PIN = 13  # BCM GPIO13 = BOARD Pin 33 (hardware PWM)

my_servo = Servo(
    SERVO_PIN,
    min_pulse_width=0.001,   # 1ms standard
    max_pulse_width=0.002    # 2ms standard
)

def move_to_angle(angle):
    """Convert angle 0-180 to gpiozero value -1 to 1."""
    value = (angle / 90.0) - 1.0
    value = max(-1.0, min(1.0, value))  # clamp to safe range
    my_servo.value = value
    print(f"Moving to {angle}° (value={value:.2f})")
    time.sleep(1.5)

print("Servo test starting...")
try:
    print("Centre 90°")
    move_to_angle(90)

    print("Full left 0°")
    move_to_angle(0)

    print("Centre 90°")
    move_to_angle(90)

    print("Full right 180°")
    move_to_angle(180)

    print("Centre 90°")
    move_to_angle(90)

except KeyboardInterrupt:
    print("Stopped.")

finally:
    my_servo.value = None
    print("Done.")
