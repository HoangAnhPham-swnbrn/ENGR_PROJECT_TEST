import time
from gpiozero import Servo

SERVO_PIN = 19

my_servo = Servo(SERVO_PIN, min_pulse_width=0.001, max_pulse_width=0.002)

print("Starting servo test. Press Ctrl+C to exit.")

try:
    print("Middle")
    my_servo.mid()
    time.sleep(1.5)

    print("Minimum")
    my_servo.min()
    time.sleep(1.5)

    print("Middle")
    my_servo.mid()
    time.sleep(1.5)

    print("Maximum")
    my_servo.max()
    time.sleep(1.5)

    print("Middle")
    my_servo.mid()
    time.sleep(1.5)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    my_servo.value = None
    print("Done.")
