#!/usr/bin/env python3
import time
import board
import busio
from adafruit_ina219 import INA219
import logging
import csv
from datetime import datetime
import os
import requests
import socket

# --- Configuration ---
I2C_ADDR_SOLAR = 0x40  # Default address
I2C_ADDR_SYSTEM = 0x41  # Soldered bridge A0

LOG_FILE = "/var/log/reduit_power.csv"
SAMPLE_INTERVAL = 5  # Seconds
SHUTDOWN_VOLTAGE = 11.5
SHUTDOWN_GRACE_PERIOD_SAMPLES = 3  # 3 samples * 5s = 15 seconds below threshold

# --- Matrix Config (Env Vars) ---
MATRIX_HOMESERVER = os.getenv("MATRIX_HOMESERVER", "https://matrix.org")
MATRIX_ACCESS_TOKEN = os.getenv("MATRIX_ACCESS_TOKEN", "")
MATRIX_ROOM_ID = os.getenv("MATRIX_ROOM_ID", "")

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_matrix_alert(message):
    """Sends a message to the configured Matrix room."""
    if not MATRIX_ACCESS_TOKEN or not MATRIX_ROOM_ID:
        logger.warning("Matrix credentials not set. Skipping alert.")
        return

    try:
        url = f"{MATRIX_HOMESERVER}/_matrix/client/r0/rooms/{MATRIX_ROOM_ID}/send/m.room.message"
        headers = {
            "Authorization": f"Bearer {MATRIX_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "msgtype": "m.text",
            "body": f"[Le Réduit Power] {message}"
        }
        # Unique txn ID to prevent duplicates (using timestamp)
        txn_id = int(time.time() * 1000)
        response = requests.put(f"{url}/{txn_id}", json=data, headers=headers, timeout=5)
        
        if response.status_code == 200:
            logger.info(f"Matrix alert sent: {message}")
        else:
            logger.error(f"Failed to send Matrix alert. Status: {response.status_code}, Resp: {response.text}")
    except Exception as e:
        logger.error(f"Exception sending Matrix alert: {e}")

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
    
    hostname = socket.gethostname()
    send_matrix_alert(f"🟢 Monitor Online on {hostname}. Voltage Check Active (> {SHUTDOWN_VOLTAGE}V).")
    logger.info("Starting Power Monitor Loop...")

    low_voltage_counter = 0

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
        # Use system voltage for battery logic (assuming system bus is V_battery)
        # Note: If solar is connected, it might boost the bus voltage. 
        # When dark, System Volts = Battery Volts.
        current_voltage = data['system_volts']
        
        msg = (f"Solar: {data['solar_volts']:.2f}V / {data['solar_watts']:.2f}W | "
               f"System: {current_voltage:.2f}V / {data['system_watts']:.2f}W | "
               f"Net: {data['net_watts']:.2f}W")
        logger.info(msg)
        
        # --- Shutdown Logic ---
        # Only check if we have a valid reading (> 0.5V) to avoid triggering on sensor failure
        if 0.5 < current_voltage < SHUTDOWN_VOLTAGE:
            low_voltage_counter += 1
            logger.warning(f"⚠️ Low Voltage detected: {current_voltage:.2f}V (Count {low_voltage_counter}/{SHUTDOWN_GRACE_PERIOD_SAMPLES})")
            
            if low_voltage_counter >= SHUTDOWN_GRACE_PERIOD_SAMPLES:
                logger.critical("🚨 CRITICAL LOW VOLTAGE - INITIATING SHUTDOWN")
                send_matrix_alert(f"🔴 CRITICAL LOW VOLTAGE ({current_voltage:.2f}V). Shutting down NOW.")
                
                # Give a moment for the network request to go out
                time.sleep(2)
                
                # Execute Shutdown
                os.system("shutdown -h now")
        else:
            # Reset counter if voltage recovers
            if low_voltage_counter > 0:
                logger.info(f"Voltage recovered ({current_voltage:.2f}V). Resetting counter.")
            low_voltage_counter = 0

        # CSV Log
        try:
            log_to_csv(data)
        except PermissionError:
            logger.error(f"Cannot write to {LOG_FILE}. Run as root or fix permissions.")

        time.sleep(SAMPLE_INTERVAL)

if __name__ == "__main__":
    main()
