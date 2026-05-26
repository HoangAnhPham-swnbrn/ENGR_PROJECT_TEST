import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(19, GPIO.OUT)

pwm = GPIO.PWM(19, 50)
pwm.start(7.5)

time.sleep(2)

pwm.stop()
GPIO.cleanup()
