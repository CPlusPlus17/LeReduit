#!/usr/bin/env python3
import time
import board
import busio
from adafruit_ina219 import INA219
import logging
import csv
from datetime import datetime

# --- Configuration ---
I2C_ADDR_SOLAR = 0x40  # Default address
I2C_ADDR_SYSTEM = 0x41  # Soldered bridge A0

LOG_FILE = "/var/log/reduit_power.csv"
SAMPLE_INTERVAL = 5  # Seconds

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_sensors(i2c):
    sensors = {}
    
    # Initialize Solar Sensor
    try:
        ina_solar = INA219(i2c, addr=I2C_ADDR_SOLAR)
        sensors['solar'] = ina_solar
        logger.info(f"Solar INA219 found at 0x{I2C_ADDR_SOLAR:02x}")
    except ValueError:
        logger.error(f"Solar INA219 NOT found at 0x{I2C_ADDR_SOLAR:02x}")

    # Initialize System Sensor
    try:
        ina_sys = INA219(i2c, addr=I2C_ADDR_SYSTEM)
        sensors['system'] = ina_sys
        logger.info(f"System INA219 found at 0x{I2C_ADDR_SYSTEM:02x}")
    except ValueError:
        logger.error(f"System INA219 NOT found at 0x{I2C_ADDR_SYSTEM:02x}")

    return sensors

def log_to_csv(data):
    file_exists = False
    try:
        with open(LOG_FILE, 'r'):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(LOG_FILE, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'solar_volts', 'solar_amps', 'solar_watts', 
                      'system_volts', 'system_amps', 'system_watts', 'net_watts']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(data)

def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    sensors = initialize_sensors(i2c)

    logger.info("Starting Power Monitor Loop...")

    while True:
        data = {
            'timestamp': datetime.now().isoformat(),
            'solar_volts': 0.0, 'solar_amps': 0.0, 'solar_watts': 0.0,
            'system_volts': 0.0, 'system_amps': 0.0, 'system_watts': 0.0,
            'net_watts': 0.0
        }

        # Read Solar
        if 'solar' in sensors:
            try:
                data['solar_volts'] = sensors['solar'].bus_voltage
                data['solar_amps'] = sensors['solar'].current / 1000.0  # Convert mA to A
                data['solar_watts'] = sensors['solar'].power / 1000.0   # Convert mW to W
            except Exception as e:
                logger.error(f"Error reading Solar INA219: {e}")

        # Read System
        if 'system' in sensors:
            try:
                data['system_volts'] = sensors['system'].bus_voltage
                data['system_amps'] = sensors['system'].current / 1000.0 # Convert mA to A
                data['system_watts'] = sensors['system'].power / 1000.0  # Convert mW to W
            except Exception as e:
                logger.error(f"Error reading System INA219: {e}")

        # Calc Net
        data['net_watts'] = data['solar_watts'] - data['system_watts']

        # Log & Print
        msg = (f"Solar: {data['solar_volts']:.2f}V / {data['solar_watts']:.2f}W | "
               f"System: {data['system_volts']:.2f}V / {data['system_watts']:.2f}W | "
               f"Net: {data['net_watts']:.2f}W")
        logger.info(msg)
        
        try:
            log_to_csv(data)
        except PermissionError:
            logger.error(f"Cannot write to {LOG_FILE}. Run as root or fix permissions.")

        time.sleep(SAMPLE_INTERVAL)

if __name__ == "__main__":
    main()
