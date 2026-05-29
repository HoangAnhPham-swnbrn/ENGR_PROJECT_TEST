import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Setup
GPIO.setup(12, GPIO.OUT)  # PWMA / E1-2
GPIO.setup(16, GPIO.OUT)  # In1
GPIO.setup(18, GPIO.OUT)  # In2

# Force everything HIGH manually
print("Setting PWMA HIGH...")
GPIO.output(12, GPIO.HIGH)  # Enable Motor A fully

print("Setting In1 HIGH, In2 LOW — Motor A forward...")
GPIO.output(16, GPIO.HIGH)
GPIO.output(18, GPIO.LOW)

sleep(3)

print("Stopping...")
GPIO.output(16, GPIO.LOW)
GPIO.output(18, GPIO.LOW)
GPIO.output(12, GPIO.LOW)

GPIO.cleanup()
