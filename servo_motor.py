from time import sleep
import RPi.GPIO as GPIO

SERVO_PIN = 5

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
    move(90)   # center
    sleep(1)
    move(85)   # slight left
    sleep(1)
    move(90)   # center
    sleep(1)
    move(95)   # slight right
    sleep(1)
    move(90)   # center

except KeyboardInterrupt:
    pass

finally:
    servo.stop()
    GPIO.cleanup()