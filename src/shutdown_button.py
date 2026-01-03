#!/usr/bin/env python3
import RPi.GPIO as GPIO
import os
import time

# Pin Definition (BCM Numbering)
SHUTDOWN_PIN = 26

def shutdown_callback(channel):
    print("Shutdown Button Pressed! Shutting down...")
    os.system("shutdown -h now")

def main():
    GPIO.setmode(GPIO.BCM)
    # Setup pin with internal Pull Up resistor.
    # Button connects Pin 26 to GND when pressed.
    GPIO.setup(SHUTDOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Add event detection (Falling edge = Button press connects to GND)
    GPIO.add_event_detect(SHUTDOWN_PIN, GPIO.FALLING, callback=shutdown_callback, bouncetime=2000)

    print(f"Shutdown Script Running. Waiting for button on GPIO {SHUTDOWN_PIN}...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Script exited.")

if __name__ == "__main__":
    main()
