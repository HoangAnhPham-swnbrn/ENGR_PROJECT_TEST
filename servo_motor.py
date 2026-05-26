import lgpio
import time

SERVO_PIN = 19
FREQUENCY = 50

chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, SERVO_PIN)

def angle_to_pw(angle):
    """Convert angle (0-180) to pulse width in microseconds"""
    angle = max(0, min(180, angle))
    return int(500 + (angle / 180) * 2000)

def move(angle):
    pw = angle_to_pw(angle)
    lgpio.tx_servo(chip, SERVO_PIN, pw, FREQUENCY)
    print(f"Moving to {angle}°")
    time.sleep(0.5)

try:
    print("Testing Servo...")

    print("Center")
    move(90)
    time.sleep(1)

    print("Left")
    move(0)
    time.sleep(1)

    print("Right")
    move(180)
    time.sleep(1)

    print("Center")
    move(90)
    time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    lgpio.tx_servo(chip, SERVO_PIN, 0)
    lgpio.gpiochip_close(chip)
    print("Done.")
