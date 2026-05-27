from gpiozero import LED
import time

right_indicators = LED(20)
left_indicators  = LED(26)
brake_lights     = LED(21)

BLINK_INTERVAL = 0.5

try:
    print("=== LED Test ===")

    # Stop Light
    print("\nStop Light ON")
    brake_lights.on()
    time.sleep(2)
    print("Stop Light OFF")
    brake_lights.off()
    time.sleep(1)

    # Left Blinkers
    print("\nLeft Blinkers")
    for _ in range(6):
        left_indicators.toggle()
        time.sleep(BLINK_INTERVAL)
    left_indicators.off()
    time.sleep(1)

    # Right Blinkers
    print("\nRight Blinkers")
    for _ in range(6):
        right_indicators.toggle()
        time.sleep(BLINK_INTERVAL)
    right_indicators.off()
    time.sleep(1)

    # Hazard Lights
    print("\nHazard Lights")
    for _ in range(10):
        left_indicators.toggle()
        right_indicators.toggle()
        time.sleep(BLINK_INTERVAL)
    left_indicators.off()
    right_indicators.off()

    print("\nTest Complete.")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    left_indicators.off()
    right_indicators.off()
    brake_lights.off()
    print("Done.")