import RPi.GPIO as GPIO
import time

# --- Configuration ---
SERVO_PIN = 19
FREQUENCY = 50  # 50Hz standard for servos

# --- Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

pwm = GPIO.PWM(SERVO_PIN, FREQUENCY)
pwm.start(0)

def angle_to_duty(angle):
    """Convert angle (0-180) to duty cycle (2-12%)"""
    angle = max(0, min(180, angle))  # Clamp to 0-180
    return 2 + (angle / 18)

def move(angle):
    """Move servo to specified angle"""
    duty = angle_to_duty(angle)
    pwm.ChangeDutyCycle(duty)
    print(f"Moving to {angle}° (duty cycle: {duty:.2f}%)")
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)  # Stop jitter

# --- Main ---
try:
    print("=== GWS S03TXF Servo Control ===")

    print("\nCenter (90°)")
    move(90)
    time.sleep(1)

    print("\nFull Left (0°)")
    move(0)
    time.sleep(1)

    print("\nCenter (90°)")
    move(90)
    time.sleep(1)

    print("\nFull Right (180°)")
    move(180)
    time.sleep(1)

    print("\nCenter (90°)")
    move(90)
    time.sleep(1)

    # --- Interactive Mode ---
    print("\n=== Interactive Mode ===")
    print("Enter angle (0-180) or 'q' to quit")

    while True:
        user_input = input("Angle: ").strip()

        if user_input.lower() == 'q':
            break

        try:
            angle = float(user_input)
            move(angle)
        except ValueError:
            print("Invalid input. Enter a number between 0 and 180.")

except KeyboardInterrupt:
    print("\nInterrupted by user.")

finally:
