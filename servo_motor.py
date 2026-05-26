from time import sleep
import RPi.GPIO as GPIO

SERVO_PIN = 19  # Changed from 5 to 19 (GPIO19, Pin 35)

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

def move(angle):
    duty = 2 + (angle / 18)
    servo.ChangeDutyCycle(duty)
    sleep(0.5)
    servo.ChangeDutyCycle(0)

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
    servo.stop()
    GPIO.cleanup()
