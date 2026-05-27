import RPi.GPIO as GPIO
import time

LED = 26

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)

try:
    print("LED ON")
    GPIO.output(LED, GPIO.HIGH)
    time.sleep(3)

    print("LED OFF")
    GPIO.output(LED, GPIO.LOW)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    GPIO.output(LED, GPIO.LOW)
    GPIO.cleanup()
    print("Done.")
