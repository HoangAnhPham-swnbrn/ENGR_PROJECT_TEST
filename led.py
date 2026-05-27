import RPi.GPIO as GPIO
import time

# --- Pin Setup ---
RIGHT_IND = 20
LEFT_IND  = 26
BRAKE     = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(RIGHT_IND, GPIO.OUT)
GPIO.setup(LEFT_IND,  GPIO.OUT)
GPIO.setup(BRAKE,     GPIO.OUT)

BLINK_INTERVAL = 0.5

try:
    print("=== LED Test ===")

    # Stop Light
    print("\nStop Light ON")
    GPIO.output(BRAKE, GPIO.HIGH)
    time.sleep(2)
    print("Stop Light OFF")
    GPIO.output(BRAKE, GPIO.LOW)
    time.sleep(1)

    # Left Blinkers
    print("\nLeft Blinkers")
    for _ in range(6):
        GPIO.output(LEFT_IND, GPIO.HIGH)
        time.sleep(BLINK_INTERVAL)
        GPIO.output(LEFT_IND, GPIO.LOW)
        time.sleep(BLINK_INTERVAL)
    time.sleep(1)

    # Right Blinkers
    print("\nRight Blinkers")
    for _ in range(6):
        GPIO.output(RIGHT_IND, GPIO.HIGH)
        time.sleep(BLINK_INTERVAL)
        GPIO.output(RIGHT_IND, GPIO.LOW)
        time.sleep(BLINK_INTERVAL)
    time.sleep(1)

    # Hazard Lights
    print("\nHazard Lights")
    for _ in range(10):
        GPIO.output(LEFT_IND,  GPIO.HIGH)
        GPIO.output(RIGHT_IND, GPIO.HIGH)
        time.sleep(BLINK_INTERVAL)
        GPIO.output(LEFT_IND,  GPIO.LOW)
        GPIO.output(RIGHT_IND, GPIO.LOW)
        time.sleep(BLINK_INTERVAL)

    print("\nTest Complete.")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    GPIO.output(RIGHT_IND, GPIO.LOW)
    GPIO.output(LEFT_IND,  GPIO.LOW)
    GPIO.output(BRAKE,     GPIO.LOW)
    GPIO.cleanup()
    print("Done.")
  
