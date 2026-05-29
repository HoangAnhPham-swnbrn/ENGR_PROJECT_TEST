from gpiozero import Motor, PWMOutputDevice
from time import sleep

# --- Motor A ---
# gpiozero Motor(forward, backward)
motor_a = Motor(forward=23, backward=24)  # BCM GPIO23=Pin16, GPIO24=Pin18
motor_b = Motor(forward=22, backward=27)  # BCM GPIO22=Pin15, GPIO27=Pin13

# Enable pins (E1-2 and E3-4) — must be HIGH for motors to run
enable_a = PWMOutputDevice(18)  # BCM GPIO18 = BOARD Pin 12
enable_b = PWMOutputDevice(17)  # BCM GPIO17 = BOARD Pin 11

def set_speed(speed):
    """Speed 0.0 to 1.0"""
    enable_a.value = speed
    enable_b.value = speed

try:
    set_speed(0.7)  # 70% speed

    print("Forward
