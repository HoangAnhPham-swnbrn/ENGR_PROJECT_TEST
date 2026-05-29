# TB6612FNG Motor A & B Test
# Using BCM GPIO numbering to match your wiring diagram

from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)          # BCM mode — matches GPIO numbers in diagram
GPIO.setwarnings(False)

# --- Pin Definitions (BCM) --- match these to your actual wiring ---
PWMA = 12       # GPIO12, Pin 32
AIN1 = 17       # GPIO17, Pin 11
AIN2 = 27       # GPIO27, Pin 13
PWMB = 13       # GPIO13, Pin 33
BIN1 = 24       # GPIO24, Pin 18
BIN2 = 25       # GPIO25, Pin 22 (adjust if STBY is here)
STBY = 4        # GPIO4,  Pin 7  — change to wherever you wired STBY

PWM_FREQ = 100  # Hz

# Setup
for pin in [PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# PWM setup
pwma = GPIO.PWM(PWMA, PWM_FREQ)
pwmb = GPIO.PWM(PWMB, PWM_FREQ)
pwma.start(0)
pwmb.start(0)

# --- Motor control functions ---
def motor_a(speed, direction="forward"):
    """Control Motor A. Speed 0–100."""
    if direction == "forward":
        GPIO.output(AIN1, GPIO.HIGH)
        GPIO.output(AIN2, GPIO.LOW)
    elif direction == "reverse":
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.HIGH)
    pwma.ChangeDutyCycle(speed)

def motor_b(speed, direction="forward"):
    """Control Motor B. Speed 0–100."""
    if direction == "forward":
        GPIO.output(BIN1, GPIO.HIGH)
        GPIO.output(BIN2, GPIO.LOW)
    elif direction == "reverse":
        GPIO.output(BIN1, GPIO.LOW)
        GPIO.output(BIN2, GPIO.HIGH)
    pwmb.ChangeDutyCycle(speed)

def stop_all():
    """Stop both motors."""
    pwma.ChangeDutyCycle(0)
    pwmb.ChangeDutyCycle(0)
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.LOW)

def standby(active=True):
    """Enable or disable TB6612FNG."""
    GPIO.output(STBY, GPIO.HIGH if active else GPIO.LOW)

# --- Test sequence ---
try:
    standby(True)           # enable motor driver

    print("Motor A forward at 75% speed")
    motor_a(75, "forward")
    sleep(3)

    print("Motor A reverse at 75% speed")
    motor_a(75, "reverse")
    sleep(3)

    print("Both motors forward at 50%")
    motor_a(50, "forward")
    motor_b(50, "forward")
    sleep(3)

    print("Stop")
    stop_all()
    sleep(1)

except KeyboardInterrupt:
    print("Interrupted")

finally:
    stop_all()
    standby(False)
    pwma.stop()
    pwmb.stop()
    GPIO.cleanup()