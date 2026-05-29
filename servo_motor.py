from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

# Use pigpio pin factory for hardware-accurate PWM
# First run: sudo pigpiod
factory = PiGPIOFactory()

SERVO_PIN = 13  # BCM GPIO13 = BOARD Pin 33

my_servo = Servo(
    SERVO_PIN,
    min_pulse_width=0.001,    # 1ms = 0°
    max_pulse_width=0.002,    # 2ms = 180°
    frame_width=0.020,        # 20ms = 50Hz standard
    pin_factory=factory
)

def move_to_angle(angle):
    """Move servo to angle 0-180."""
    value = (angle / 90.0) - 1.0
    value = max(-1.0, min(1.0, value))
    my_servo.value = value
    print(f"Moving to {angle}°")
    sleep(1.0)

try:
    print("Centre 90°")
    move_to_angle(90)
    sleep(1)

    print("Full left 0°")
    move_to_angle(0)
    sleep(1)

    print("Centre 90°")
    move_to_angle(90)
    sleep(1)

    print("Full right 180°")
    move_to_angle(180)
    sleep(1)

    print("Centre 90°")
    move_to_angle(90)

except KeyboardInterrupt:
    print("Stopped.")

finally:
    my_servo.value = None
    print("Done.")
