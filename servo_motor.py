import pigpio
from time import sleep

pi = pigpio.pi()

SERVO_PIN = 5

def move(angle):
    # Convert angle to pulsewidth
    # 500 = 0°, 1500 = 90°, 2500 = 180°
    pulsewidth = 500 + (angle / 180) * 2000
    pi.set_servo_pulsewidth(SERVO_PIN, pulsewidth)
    sleep(0.5)

try:
    print("Center 90")
    move(90)
    sleep(1)

    print("Left 45")
    move(45)
    sleep(1)

    print("Center 90")
    move(90)
    sleep(1)

    print("Right 135")
    move(135)
    sleep(1)

    print("Center 90")
    move(90)
    sleep(1)

finally:
    pi.set_servo_pulsewidth(SERVO_PIN, 0)  # stop signal
    pi.stop()
