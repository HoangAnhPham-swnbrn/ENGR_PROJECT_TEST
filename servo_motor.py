import RPi.GPIO as GPIO
import time

SERVO_PIN = 19

GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def move(angle):
    duty = 2 + (angle / 18)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)

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

except KeyboardInterrupt:
    pass

finally:
    pwm.stop()
    GPIO.cleanup()
    print("Done.")
