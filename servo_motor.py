import pigpio
import time

# --- Configuration ---
SERVO_PIN = 19
MIN_PW = 500    # Minimum pulse width in microseconds (0°)
MAX_PW = 2500   # Maximum pulse width in microseconds (180°)
MID_PW = 1500   # Midpoint pulse width (90°)

# --- Setup ---
pi = pigpio.pi()

if not pi.connected:
    print("Failed to connect to pigpio daemon. Run: sudo systemctl start pigpiod")
    exit()

def angle_to_pw(angle):
    """Convert angle (0-180) to pulse width (500-2500 microseconds)"""
    angle = max(0, min(180, angle))  # Clamp angle to 0-180
    return int(MIN_PW + (angle / 180) * (MAX_PW - MIN_PW))

def move(angle):
    """Move servo to specified angle"""
    pw = angle_to_pw(angle)
    pi.set_servo_pulsewidth(SERVO_PIN, pw)
    print(f"Moving to {angle}° (pulse width: {pw}µs)")
    time.sleep(0.5)

def stop_servo():
    """Stop sending pulses to servo (reduces jitter/heat)"""
    pi.set_servo_pulsewidth(SERVO_PIN, 0)

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
            stop_servo()  # Stop pulse after reaching position
        except ValueError:
            print("Invalid input. Enter a number between 0 and 180.")

except KeyboardInterrupt:
    print("\nInterrupted by user.")

finally:
    stop_servo()
    pi.stop()
    print("Cleanup done.")
