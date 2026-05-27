import lgpio
import time

LEFT_BLINKER  = 20
RIGHT_BLINKER = 21
BLINK_INTERVAL = 0.5

chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, LEFT_BLINKER)
lgpio.gpio_claim_output(chip, RIGHT_BLINKER)

try:
    print("=== Blinker Test ===")

    print("\nLeft Blinker")
    for _ in range(6):
        lgpio.gpio_write(chip, LEFT_BLINKER, 1)
        time.sleep(BLINK_INTERVAL)
        lgpio.gpio_write(chip, LEFT_BLINKER, 0)
        time.sleep(BLINK_INTERVAL)

    time.sleep(1)

    print("\nRight Blinker")
    for _ in range(6):
        lgpio.gpio_write(chip, RIGHT_BLINKER, 1)
        time.sleep(BLINK_INTERVAL)
        lgpio.gpio_write(chip, RIGHT_BLINKER, 0)
        time.sleep(BLINK_INTERVAL)

    print("\nDone.")

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    lgpio.gpio_write(chip, LEFT_BLINKER,  0)
    lgpio.gpio_write(chip, RIGHT_BLINKER, 0)
    lgpio.gpiochip_close(chip)
    print("Cleanup done.")
