import lgpio
from time import sleep

SERVO_PIN = 5
h = lgpio.gpiochip_open(0)

def move(angle):
    pulsewidth = 500 + (angle / 180) * 2000
    lgpio.tx_servo(h, SERVO_PIN, int(pulsewidth))
    sleep(0.5)

try:
    print("Center")
    move(90)
    sleep(1)

    print("Left")
    move(45)
    sleep(1)

    print("Center")
    move(90)
    sleep(1)

    print("Right")
    move(135)
    sleep(1)

    print("Center")
    move(90)

finally:
    lgpio.tx_servo(h, SERVO_PIN, 0)
    lgpio.gpiochip_close(h)
