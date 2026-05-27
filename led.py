import lgpio
import time

BLINKER = 26
BLINK_INTERVAL = 0.5

chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, BLINKER)

try:
    print("=== Blinker Test ===")

    for _ in range(10):
        lgpio.gpio_write(chip, BLINKER, 1)
        time.sleep(BLINK_INTERVAL)
        lgpio.gpio_write(chip, BLINKER, 0)
        time.sleep(BLINK_INTERVAL)

    print("Done.")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    lgpio.gpio_write(chip, BLINKER, 0)
    lgpio.gpiochip_close(chip)
    print("Cleanup done.")
