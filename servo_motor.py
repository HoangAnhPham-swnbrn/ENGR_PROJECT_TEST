import time
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory # Not needed for Pi 5 default, gpiozero handles it via gpiod

# Define the GPIO pin connected to the servo signal wire
SERVO_PIN = 14

# Standard hobby servos expect a pulse width between 1ms and 2ms (0.001s to 0.002s).
# If your servo doesn't reach full 180 or jitters, adjust min_pulse_width and max_pulse_width.
my_servo = Servo(SERVO_PIN, min_pulse_width=0.001, max_pulse_width=0.002)

print("Starting servo sweep program. Press Ctrl+C to exit.")

try:
    while True:
        # Move to minimum position (-1)
        print("Moving to Minimum")
        my_servo.min()
        time.sleep(1.5)

        # Move to middle position (0)
        print("Moving to Middle")
        my_servo.mid()
        time.sleep(1.5)

        # Move to maximum position (1)
        print("Moving to Maximum")
        my_servo.max()
        time.sleep(1.5)

except KeyboardInterrupt:
    print("\nProgram stopped by user. Cleaning up...")
    # Detach the servo to stop it from drawing idle power/buzzing
    my_servo.value = None
