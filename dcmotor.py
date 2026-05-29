# L293D Motor Test — Forward, Stop, Reverse
# BOARD pin numbering

from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# --- Pin Definitions ---
PWMA = 12       # E1-2
AIN1 = 16       # In1
AIN2 = 18       # In2
PWMB = 11       # E3-4
BIN1 = 15       # In3
BIN2 = 13       # In4

PWM_FREQ = 100

# --- Setup ---
for pin in [PWMA, AIN1, AIN2, PWMB, BIN1, BIN2]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

pwma = GPIO.PWM(PWMA, PWM_FREQ)
pwmb = GPIO.PWM(PWMB, PWM_FREQ)
pwma.start(0)
pwmb.start(0)

# --- Functions ---
def motor_a(speed, direction="forward"):
    if direction == "forward":
        GPIO.output(AIN1, GPIO.HIGH)
        GPIO.output(AIN2, GPIO.LOW)
    elif direction == "reverse":
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.HIGH)
    elif direction == "stop":
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.LOW)
    pwma.ChangeDutyCycle(speed)

def motor_b(speed, direction="forward"):
    if direction == "forward":
        GPIO.output(BIN1, GPIO.HIGH)
        GPIO.output(BIN2, GPIO.LOW)
    elif direction == "reverse":
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.HIGH)
    elif direction == "stop":
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.LOW)
    pwmb.ChangeDutyCycle(speed)

def stop_all():
    motor_a(0, "stop")
    motor_b(0, "stop")

# --- Test Sequence ---
try:
    print("Forward 3 seconds...")
    motor_a(70, "forward")
    motor_b(70, "forward")
    sleep(3)

    print("Stopping 2 seconds...")
    stop_all()
    sleep(2)

    print("Reverse 3 seconds...")
    motor_a(70, "reverse")
    motor_b(70, "reverse")
    sleep(3)

    print("Stopping...")
    stop_all()

except KeyboardInterrupt:
    print("Interrupted")

finally:
    stop_all()
    pwma.stop()
    pwmb.stop()
    GPIO.cleanup()
