import pigpio
from time import sleep

pi = pigpio.pi()

# --- Pin Definitions (BCM for pigpio) ---
PWMA = 18      # BCM GPIO18 = BOARD Pin 12
AIN1 = 23      # BCM GPIO23 = BOARD Pin 16
AIN2 = 24      # BCM GPIO24 = BOARD Pin 18
PWMB = 17      # BCM GPIO17 = BOARD Pin 11
BIN1 = 22      # BCM GPIO22 = BOARD Pin 15
BIN2 = 27      # BCM GPIO27 = BOARD Pin 13

SPEED = 150    # 0-255 for pigpio

# --- Setup ---
for pin in [AIN1, AIN2, BIN1, BIN2]:
    pi.set_mode(pin, pigpio.OUTPUT)
    pi.write(pin, 0)

def motor_a(speed, direction="forward"):
    if direction == "forward":
        pi.write(AIN1, 1)
        pi.write(AIN2, 0)
    elif direction == "reverse":
        pi.write(AIN1, 0)
        pi.write(AIN2, 1)
    elif direction == "stop":
        pi.write(AIN1, 0)
        pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, speed)

def motor_b(speed, direction="forward"):
    if direction == "forward":
        pi.write(BIN1, 1)
        pi.write(BIN2, 0)
    elif direction == "reverse":
        pi.write(BIN1, 0)
        pi.write(BIN2, 1)
    elif direction == "stop":
        pi.write(BIN1, 0)
        pi.write(BIN2, 0)
    pi.set_PWM_dutycycle(PWMB, speed)

def stop_all():
    motor_a(0, "stop")
    motor_b(0, "stop")

# --- Test ---
try:
    print("Forward 3 seconds...")
    motor_a(SPEED, "forward")
    motor_b(SPEED, "forward")
    sleep(3)

    print("Stopping 2 seconds...")
    stop_all()
    sleep(2)

    print("Reverse 3 seconds...")
    motor_a(SPEED, "reverse")
    motor_b(SPEED, "reverse")
    sleep(3)

    print("Stopping...")
    stop_all()

except KeyboardInterrupt:
    print("Interrupted")

finally:
    stop_all()
    pi.stop()
