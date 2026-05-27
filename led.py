import RPi.GPIO as GPIO
import time

BRAKE = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(BRAKE, GPIO.OUT)

try:
    print("Stop Light ON")
    GPIO.output(BRAKE, GPIO.HIGH)
    time.sleep(3)

    print("Stop Light OFF")
    GPIO.output(BRAKE, GPIO.LOW)
    time.sleep(1)

    print("Done.")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    GPIO.output(BRAKE, GPIO.LOW)
    GPIO.cleanup()
