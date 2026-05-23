from time import sleep
import RPi.GPIO as GPIO

# -----------------------------
# Servo wiring
# -----------------------------
# White servo signal wire:
# Raspberry Pi physical pin 29 = GPIO5
SERVO_PIN = 5

# Servo angle settings
LEFT_ANGLE = 45
CENTER_ANGLE = 90
RIGHT_ANGLE = 135

# -----------------------------
# GPIO setup
# -----------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Servo uses 50 Hz PWM
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)


def set_servo_angle(angle):
    """
    Move servo to a given angle.
    angle should be between 0 and 180 degrees.
    """

    # Convert angle to duty cycle
    # 0 degrees   ≈ 2.5%
    # 90 degrees  ≈ 7.5%
    # 180 degrees ≈ 12.5%
    duty_cycle = 2.5 + (angle / 180) * 10

    servo.ChangeDutyCycle(duty_cycle)
    sleep(0.7)

    # Stop sending signal to reduce jitter
    servo.ChangeDutyCycle(0)
    sleep(0.2)


try:
    print("Move to center")
    set_servo_angle(CENTER_ANGLE)
    sleep(1)

    print("Turn left")
    set_servo_angle(LEFT_ANGLE)
    sleep(1)

    print("Return to center")
    set_servo_angle(CENTER_ANGLE)
    sleep(1)

    print("Turn right")
    set_servo_angle(RIGHT_ANGLE)
    sleep(1)

    print("Return to center")
    set_servo_angle(CENTER_ANGLE)
    sleep(1)

    print("Turn left")
    set_servo_angle(LEFT_ANGLE)
    sleep(1)

    print("Turn right")
    set_servo_angle(RIGHT_ANGLE)
    sleep(1)

    print("Final return to center")
    set_servo_angle(CENTER_ANGLE)
    sleep(1)

except KeyboardInterrupt:
    print("Program stopped by user")

finally:
    servo.stop()
    GPIO.cleanup()
    print("GPIO cleaned up")