from time import sleep
from gpiozero import Servo
from gpiozero.pins.lgpio import LGPIOFactory

factory = LGPIOFactory()

servo = Servo(5, pin_factory=factory,
              min_pulse_width=0.5/1000,
              max_pulse_width=2.5/1000)

def move(value):
    # value: -1 = full left, 0 = center, 1 = full right
    servo.value = value
    sleep(0.5)

try:
    move(0)      # center
    sleep(1)
    move(-0.1)   # slight left
    sleep(1)
    move(0)      # center
    sleep(1)
    move(0.1)    # slight right
    sleep(1)
    move(0)      # center

finally:
    servo.detach()
