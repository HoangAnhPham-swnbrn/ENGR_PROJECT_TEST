from gpiozero import LED
import time

led = LED(26)  # Test stop light first

print("ON")
led.on()
time.sleep(2)

print("OFF")
led.off()
time.sleep(1)

print("Done.")
