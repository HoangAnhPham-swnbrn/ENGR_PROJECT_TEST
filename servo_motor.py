import time
from gpiozero import Servo

SERVO_PIN = 13  # BCM GPIO13 = BOARD Pin 33

my_servo = Servo(
    SERVO_PIN,
    min_pulse_width=0.001,   # 1ms — standard minimum
    max_pulse_width=0.002    # 2ms — standard maximum
)

def move_to_angle(angle):
    value = (angle / 90) - 1
    my_servo.value = value
    print(f"Moving to {angle}°")
    time.sleep(1.5)

print("Starting servo test. Press Ctrl+C to exit.")
try:
    print("Center 90°")
    move_to_angle(90)

    print("Rotate Left 0°")
    move_to_angle(0)

    print("Back to Center 90°")
    move_to_angle(90)

    print("Rotate Right 180°")
    move_to_angle(180)

    print("Back to Center 90°")
    move_to_angle(90)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    my_servo.value = None
    print("Done.")
