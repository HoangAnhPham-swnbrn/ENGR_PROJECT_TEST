import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

SERVO_PIN = 33  # BOARD Pin 33 = BCM GPIO13

GPIO.setup(SERVO_PIN, GPIO.OUT)

# Servo PWM at 50Hz
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

def set_angle(angle):
    """Set servo angle 0–180 degrees."""
    # Convert angle to duty cycle (2.5% = 0°, 12.5% = 180°)
    duty = 2.5 + (angle / 180.0) * 10.0
    servo.ChangeDutyCycle(duty)
    time.sleep(0.3)   # wait for servo to reach position
    servo.ChangeDutyCycle(0)  # stop sending signal to prevent jitter

try:
    print("Centre (90°)...")
    set_angle(90)
    time.sleep(1)

    print("Full left (0°)...")
    set_angle(0)
    time.sleep(1)

    print("Full right (180°)...")
    set_angle(180)
    time.sleep(1)

    print("Back to centre (90°)...")
    set_angle(90)
    time.sleep(1)

    print("Done.")

except KeyboardInterrupt:
    print("Interrupted")

finally:
    servo.stop()
    GPIO.cleanup()
