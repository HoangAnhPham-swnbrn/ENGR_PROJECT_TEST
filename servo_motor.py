from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

factory = PiGPIOFactory()

# min_pulse_width and max_pulse_width tuned for GWS servo
servo = Servo(19, min_pulse_width=1/1000, max_pulse_width=2/1000, pin_factory=factory)

def move(angle):
    # Convert 0-180 to gpiozero's -1 to 1 range
    value = (angle / 90) - 1
    servo.value = value
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

except KeyboardInterrupt:
    pass

finally:
    servo.detach()
