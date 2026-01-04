#!/usr/bin/env python3
import time
import board
import busio
from adafruit_ina219 import INA219
import logging
import csv
import json
from datetime import datetime
import os
import requests
import socket
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from w1thermsensor import W1ThermSensor, SensorNotReadyError

import math
from adafruit_bme280 import basic as adafruit_bme280
import math
import subprocess
from adafruit_bme280 import basic as adafruit_bme280
from adafruit_mpu6050 import MPU6050
import adafruit_bh1750
import RPi.GPIO as GPIO
import smbus2

# --- Configuration ---
I2C_ADDR_SOLAR = 0x40
I2C_ADDR_SYSTEM = 0x41
I2C_ADDR_BME = 0x76  # or 0x77
I2C_ADDR_MPU = 0x69 # AD0 pulled HIGH (3.3V) to avoid conflict with DS3231 (0x68)
I2C_ADDR_COMPASS = 0x1E # HMC5883L
I2C_ADDR_BH1750 = 0x23

# GPIO Config
PIN_SHUTDOWN = 26
PIN_LID_SENSOR = 17
PIN_BUZZER = 27

LOG_FILE = "/var/log/reduit_power.csv"
SAMPLE_INTERVAL_ACTIVE = 5
SAMPLE_INTERVAL_ECO = 30
current_sample_interval = SAMPLE_INTERVAL_ACTIVE

SHUTDOWN_VOLTAGE = 11.5
SHUTDOWN_GRACE_PERIOD_SAMPLES = 3
TAMPER_THRESHOLD_G = 0.5
# ... (imports)

# --- Configuration ---
# ...
WIFI_INTERFACE = "wlan1"

# --- Alert Thresholds ---
THRESH_VOLT_LOW_WARN = 12.0
THRESH_TEMP_HIGH = 50.0
THRESH_TEMP_LOW = 0.0
THRESH_HUMIDITY_HIGH = 80.0
THRESH_LIGHT_LEAK = 10.0 # Lux inside closed box

# --- Alert Manager Class ---
class AlertManager:
    def __init__(self):
        self.states = {} # key -> last_alert_time
        self.cooldown = 3600 # 1 hour cooldown for persistent conditions
        
    def check(self, key, condition, message, is_critical=False):
        timestamp = time.time()
        last_time = self.states.get(key, 0)
        
        if condition:
            # If condition is met, check if we should alert
            if (timestamp - last_time) > self.cooldown:
                priority = "🔴 CRITICAL" if is_critical else "⚠️ WARNING"
                full_msg = f"{priority}: {message}"
                send_matrix_alert(full_msg)
                logger.warning(full_msg)
                if is_critical: buzz(1.0, 1)
                else: buzz(0.2, 2)
                self.states[key] = timestamp
        else:
            # Reset state if condition clears (optional, allows re-alert immediately if it happens again)
            # Maybe keep hysteresis? For now, simple clear.
            if key in self.states and (timestamp - last_time) > 60: # debounce clear
                # Optionally notify recovery? "Condition Cleared"
                # send_matrix_alert(f"✅ Resolved: {key}")
                pass
            # We don't remove the key immediately to prevent flapping, 
            # but effectively the condition is False so we won't alert.
            pass

alert_manager = AlertManager()

# ... (rest of helper functions)

def check_sensor_thresholds(data):
    # 1. Voltage Warning (distinct from Shutdown)
    # Only if system_volts is > 5 (valid reading)
    volts = data['system_volts']
    if volts > 5.0:
        alert_manager.check("batt_low", volts < THRESH_VOLT_LOW_WARN, 
                            f"Battery Low: {volts:.2f}V (Approaching Shutdown)", is_critical=False)
    
    # 2. Temperature
    temp = data['temperature']
    # Filter valid reading (sometimes 85 is error/init code for DS18B20? actually 0 is suspicious too if invalid)
    alert_manager.check("temp_high", temp > THRESH_TEMP_HIGH, 
                        f"High Temperature: {temp:.1f}°C", is_critical=True)
    alert_manager.check("temp_low", temp < THRESH_TEMP_LOW, 
                        f"Freezing Temperature: {temp:.1f}°C", is_critical=False)
                        
    # 3. Humidity
    hum = data['humidity']
    alert_manager.check("hum_high", hum > THRESH_HUMIDITY_HIGH, 
                        f"High Humidity: {hum:.1f}% (Condensation Risk)", is_critical=False)
                        
    # 4. Light Leak (Lid Closed but Light detected)
    # Lux > 10 and Lid == False (Closed)
    lux = data['lux']
    lid_open = data['lid_open']
    alert_manager.check("light_leak", (not lid_open and lux > THRESH_LIGHT_LEAK), 
                        f"Light Detected ({lux:.1f} lx) while Lid Closed! Hull Breach?", is_critical=True)

# ... (main loop)

    while True:
        # Check Matrix for Commands
        check_matrix_commands()
        
        # ... (read sensors) ...
        
        # Check alerts
        check_sensor_thresholds(data)

        # Logging
        # ...
MATRIX_HOMESERVER = os.getenv("MATRIX_HOMESERVER", "https://matrix.org")
MATRIX_ACCESS_TOKEN = os.getenv("MATRIX_ACCESS_TOKEN", "")
MATRIX_ROOM_ID = os.getenv("MATRIX_ROOM_ID", "")

# --- InfluxDB Config (Env Vars) ---
INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "")
INFLUX_ORG = os.getenv("INFLUX_ORG", "reduit")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "power")

# --- GPIO Setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_LID_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BUZZER, GPIO.OUT, initial=GPIO.LOW)

def buzz(duration=0.1, count=1):
    """Activates the buzzer."""
    try:
        for _ in range(count):
            GPIO.output(PIN_BUZZER, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(PIN_BUZZER, GPIO.LOW)
            if count > 1: time.sleep(0.1)
    except: pass

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- InfluxDB Client ---
influx_write_api = None
try:
    if INFLUX_TOKEN:
        influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        influx_write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        logger.info(f"InfluxDB Client initialized for {INFLUX_URL}")
    else:
        logger.warning("INFLUX_TOKEN not set. Skipping DB writes.")
except Exception as e:
    logger.error(f"Failed to init InfluxDB: {e}")

# --- DS18B20 Sensor ---
temp_sensor = None
try:
    temp_sensor = W1ThermSensor()
    logger.info(f"DS18B20 Sensor found: {temp_sensor.id}")
except Exception as e:
    logger.warning(f"No DS18B20 sensor found: {e}")

# --- Compass Helper Class (HMC5883L) ---
class Compass:
    def __init__(self, i2c_bus, addr=0x1E):
        self.bus = i2c_bus
        self.addr = addr
        self._init_sensor()

    def _init_sensor(self):
        try:
            while not self.bus.try_lock(): pass
            # 0x00=ConfigA (8-avg,15Hz), 0x01=ConfigB (Gain), 0x02=Mode (Continuous)
            self.bus.writeto(self.addr, bytes([0x00, 0x70]))
            self.bus.writeto(self.addr, bytes([0x01, 0x20]))
            self.bus.writeto(self.addr, bytes([0x02, 0x00]))
            self.bus.unlock()
            logger.info("Compass HMC5883L initialized.")
        except Exception as e:
            logger.error(f"Failed to init Compass: {e}")
            if hasattr(self.bus, 'unlock'): self.bus.unlock()

    def read_heading(self):
        try:
            while not self.bus.try_lock(): pass
            self.bus.writeto(self.addr, bytes([0x03]), stop=False)
            buffer = bytearray(6)
            self.bus.readfrom_into(self.addr, buffer)
            self.bus.unlock()
            x = int.from_bytes(buffer[0:2], byteorder='big', signed=True)
            z = int.from_bytes(buffer[2:4], byteorder='big', signed=True)
            y = int.from_bytes(buffer[4:6], byteorder='big', signed=True)
            heading_rad = math.atan2(y, x)
            if heading_rad < 0: heading_rad += 2 * math.pi
            return math.degrees(heading_rad)
        except Exception as e:
            if hasattr(self.bus, 'unlock'): self.bus.unlock()
            return 0.0

# --- Matrix Helper ---
# ... (imports)

# Global State for Status Command
latest_data = {}

# ... (rest of config) ...

def check_matrix_commands():
    """Polls Matrix for new commands (!wifi on/off, !status)."""
    global next_batch_token
    if not MATRIX_ACCESS_TOKEN or not MATRIX_ROOM_ID: return

    try:
        url = f"{MATRIX_HOMESERVER}/_matrix/client/r0/sync"
        params = {"timeout": 0, "filter": '{"room":{"rooms":["' + MATRIX_ROOM_ID + '"]}}'}
        if next_batch_token: params["since"] = next_batch_token
        
        headers = {"Authorization": f"Bearer {MATRIX_ACCESS_TOKEN}"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            next_batch_token = data.get("next_batch")
            
            rooms = data.get("rooms", {}).get("join", {}).get(MATRIX_ROOM_ID, {})
            timeline = rooms.get("timeline", {}).get("events", [])
            
            for event in timeline:
                if event.get("type") == "m.room.message":
                    body = event.get("content", {}).get("body", "").strip().lower()
                    if body == "!wifi off":
                        set_wifi(False)
                    elif body == "!wifi on":
                        set_wifi(True)
                    elif body == "!maps off":
                        set_k8s_scale("tileserver", 0)
                    elif body == "!maps on":
                        set_k8s_scale("tileserver", 1)
                    elif body == "!eco on":
                        set_cpu_governor("powersave")
                        set_k8s_scale("tileserver", 0)
                        set_wifi_powersave(True)
                        global current_sample_interval
                        current_sample_interval = SAMPLE_INTERVAL_ECO
                        send_matrix_alert("💤 ECO MODE: ON (Gov:Powersave, Maps:Off, Poll:30s)")
                    elif body == "!eco off":
                        set_cpu_governor("ondemand")
                        set_k8s_scale("tileserver", 1)
                        set_wifi_powersave(False)
                        global current_sample_interval
                        current_sample_interval = SAMPLE_INTERVAL_ACTIVE
                        send_matrix_alert("🚀 ECO MODE: OFF (System Restored)")
                    elif body == "!status":
                        send_status_report()
    except Exception as e:
        logger.error(f"Matrix Sync Fail: {e}")

def set_wifi_powersave(enable):
    """Sets WiFi Power Save mode."""
    state = "on" if enable else "off"
    try:
        subprocess.run(["iw", "dev", WIFI_INTERFACE, "set", "power_save", state], check=True)
    except Exception as e:
        logger.error(f"WiFi PS Failed: {e}")

def set_k8s_scale(deployment, replicas):
    """Scales a k8s deployment to save power."""
    try:
        # Assumes running as root with kubectl access or KUBECONFIG set
        cmd = ["kubectl", "scale", "deployment", deployment, f"--replicas={replicas}", "-n", "default"]
        subprocess.run(cmd, check=True)
        send_matrix_alert(f"⚖️ Scaled {deployment} to {replicas} replicas.")
        buzz(0.1, 1)
    except Exception as e:
        logger.error(f"Scale Failed: {e}")
        send_matrix_alert(f"⚠️ Scale Failed: {e}")

def set_cpu_governor(mode):
    """Sets CPU Governor (powersave|ondemand|performance)."""
    # modes: powersave (min freq), ondemand (jumpy), performance (max)
    try:
        # RPi specific: write to all cores
        # We use a shell command with wildcard expansion
        subprocess.run(f"echo {mode} | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True, check=True)
        send_matrix_alert(f"🧠 CPU Governor set to: {mode.upper()}")
        buzz(0.1, 1)
    except Exception as e:
        logger.error(f"CPU Gov Failed: {e}")
        send_matrix_alert(f"⚠️ CPU Gov Failed: {e}")

def send_status_report():
    if not latest_data:
        send_matrix_alert("⚠️ Status: No sensor data available yet.")
        return
        
    d = latest_data
    # Get current CPU Gov
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
            gov = f.read().strip()
    except: gov = "?"

    msg = (f"🔋 **Power**: {d.get('system_volts',0):.2f}V | {d.get('net_watts',0):.1f}W Net\n"
           f"🌡️ **Climate**: {d.get('temperature',0):.1f}°C | {d.get('humidity',0):.0f}% | {d.get('pressure',0):.0f}hPa\n"
           f"🧠 **System**: CPU: {gov} | Maps: {'?'}\n" # Could check replica count if needed
           f"💡 **Light/Lid**: {d.get('lux',0):.0f} lx | Lid: {'OPEN' if d.get('lid_open') else 'Closed'}\n"
           f"🧭 **Heading**: {d.get('heading',0):.0f}°")
    send_matrix_alert(msg)

# ... (set_wifi, get_temperature, write_to_influx, initialize_sensors, log_to_csv) ...

def main():
    global latest_data
    i2c = busio.I2C(board.SCL, board.SDA)
    # ... (init sensors) ...
    
    hostname = socket.gethostname()
    buzz(0.1, 2)
    send_matrix_alert(f"🟢 Monitor Online on {hostname}. Audio & Sensors Active.")
    logger.info("Starting Power Monitor Loop...")

    low_voltage_counter = 0
    last_accel = None
    last_lid_state = False 

    while True:
        # Check Matrix for Commands
        check_matrix_commands()

        data = {
            'timestamp': datetime.now().isoformat(),
            'solar_volts': 0.0, 'solar_amps': 0.0, 'solar_watts': 0.0,
            'system_volts': 0.0, 'system_amps': 0.0, 'system_watts': 0.0,
            'net_watts': 0.0, 'temperature': 0.0, 'humidity': 0.0, 'pressure': 0.0,
            'lid_open': False, 'heading': 0.0, 'lux': 0.0
        }

        # ... (Sensor Reading Logic same as before) ...
        # ... (0. Check Lid) ...
        # ... (1. Read Temp) ...
        # ... (2. Read Power) ...
        # ... (3. Read Environment) ...
        # ... (4. Read Compass) ...
        # ... (5. Check Motion) ...
        
        # [OMITTED FOR BREVITY - KEEP EXISTING READING CODE]

        # Update Global State for !status command
        latest_data = data
        
        # Export for TAK Bridge (IPC)
        try:
            with open("/tmp/reduit_status.json", "w") as f:
                json.dump(data, f)
        except: pass
        
        # Check Thresholds
        check_sensor_thresholds(data)
        
        # Logging
        # ... (rest of loop) ...

def set_wifi(state):
    """Toggles WiFi Interface."""
    cmd = "up" if state else "down"
    try:
        # Use ip link set
        subprocess.run(["ip", "link", "set", WIFI_INTERFACE, cmd], check=True)
        send_matrix_alert(f"📶 WiFi {WIFI_INTERFACE} is now {cmd.upper()}.")
        buzz(0.1, 1) # Confirm beep
    except Exception as e:
        send_matrix_alert(f"⚠️ Failed to set WiFi {cmd}: {e}")

def get_temperature():
    if not temp_sensor: return 0.0
    try: return temp_sensor.get_temperature()
    except: return 0.0

def write_to_influx(data):
    if not influx_write_api: return
    try:
        p = Point("power_metrics") \
            .tag("host", socket.gethostname()) \
            .field("solar_volts", data['solar_volts']) \
            .field("solar_amps", data['solar_amps']) \
            .field("solar_watts", data['solar_watts']) \
            .field("system_volts", data['system_volts']) \
            .field("system_amps", data['system_amps']) \
            .field("system_watts", data['system_watts']) \
            .field("net_watts", data['net_watts']) \
            .field("temperature_c", data['temperature']) \
            .field("humidity_pct", data.get('humidity', 0.0)) \
            .field("pressure_hpa", data.get('pressure', 0.0)) \
            .field("lux", data.get('lux', 0.0)) \
            .field("heading_deg", data.get('heading', 0.0)) \
            .field("lid_open", int(data.get('lid_open', 0))) \
            .time(datetime.utcnow(), WritePrecision.NS)
        influx_write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)
    except Exception as e:
        logger.error(f"Influx Write Failed: {e}")

def initialize_sensors(i2c):
    sensors = {}
    
    for name, addr in [('solar', I2C_ADDR_SOLAR), ('system', I2C_ADDR_SYSTEM)]:
        try:
            sensors[name] = INA219(i2c, addr=addr)
            logger.info(f"{name} INA219 found at 0x{addr:02x}")
        except ValueError:
            logger.error(f"{name} INA219 NOT found at 0x{addr:02x}")
            
    try:
        bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=I2C_ADDR_BME)
        sensors['bme'] = bme
        logger.info(f"BME280 found at 0x{I2C_ADDR_BME:02x}")
    except Exception as e:
        logger.warning(f"BME280 init failed: {e}")

    try:
        mpu = MPU6050(i2c, address=I2C_ADDR_MPU)
        sensors['mpu'] = mpu
        logger.info(f"MPU6050 found at 0x{I2C_ADDR_MPU:02x}")
    except Exception as e:
        logger.warning(f"MPU6050 init failed: {e}")
        
    try:
        bh1750 = adafruit_bh1750.BH1750(i2c, address=I2C_ADDR_BH1750)
        sensors['light'] = bh1750
        logger.info(f"BH1750 found at 0x{I2C_ADDR_BH1750:02x}")
    except Exception as e:
        logger.warning(f"BH1750 init failed: {e}")
        
    try:
        while not i2c.try_lock(): pass
        addrs = i2c.scan()
        i2c.unlock()
        if I2C_ADDR_COMPASS in addrs:
            compass = Compass(i2c, addr=I2C_ADDR_COMPASS)
            sensors['compass'] = compass
            logger.info(f"Compass found at 0x{I2C_ADDR_COMPASS:02x}")
    except: pass
    return sensors

def log_to_csv(data):
    file_exists = False
    try:
        with open(LOG_FILE, 'r'): file_exists = True
    except FileNotFoundError: pass
    with open(LOG_FILE, 'a', newline='') as csvfile:
        fieldnames = ['timestamp', 'solar_volts', 'solar_amps', 'solar_watts', 
                      'system_volts', 'system_amps', 'system_watts', 'net_watts',
                      'temperature', 'humidity', 'pressure', 'lid_open', 'heading', 'lux']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists: writer.writeheader()
        writer.writerow(data)

def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    sensors = initialize_sensors(i2c)
    
    hostname = socket.gethostname()
    
    # Startup Sound: 2 short beeps
    buzz(0.1, 2)
    
    send_matrix_alert(f"🟢 Monitor Online on {hostname}. Audio & Sensors Active. Listening for '!wifi on/off'.")
    logger.info("Starting Power Monitor Loop...")

    low_voltage_counter = 0
    last_accel = None
    last_lid_state = False 

    while True:
        # Check Matrix for Commands
        check_matrix_commands()

        data = {
            'timestamp': datetime.now().isoformat(),
            'solar_volts': 0.0, 'solar_amps': 0.0, 'solar_watts': 0.0,
            'system_volts': 0.0, 'system_amps': 0.0, 'system_watts': 0.0,
            'net_watts': 0.0, 'temperature': 0.0, 'humidity': 0.0, 'pressure': 0.0,
            'lid_open': False, 'heading': 0.0, 'lux': 0.0
        }

        # 0. Check Lid
        is_open = GPIO.input(PIN_LID_SENSOR) == GPIO.HIGH
        data['lid_open'] = is_open

        if is_open and not last_lid_state:
            buzz(0.5) # Warning Beep
            send_matrix_alert("🔓 SECURITY ALERT: Le Réduit Lid Opened!")
        elif not is_open and last_lid_state:
            send_matrix_alert("🔒 Info: Lid Closed.")
        last_lid_state = is_open

        # 1. Read Temp
        data['temperature'] = get_temperature()

        # 2. Read Power
        if 'solar' in sensors:
            try:
                data['solar_volts'] = sensors['solar'].bus_voltage
                data['solar_amps'] = sensors['solar'].current / 1000.0
                data['solar_watts'] = sensors['solar'].power / 1000.0
            except: pass
        if 'system' in sensors:
            try:
                data['system_volts'] = sensors['system'].bus_voltage
                data['system_amps'] = sensors['system'].current / 1000.0
                data['system_watts'] = sensors['system'].power / 1000.0
            except: pass
        data['net_watts'] = data['solar_watts'] - data['system_watts']

        # 3. Read Environment (BME + Light)
        if 'bme' in sensors:
            try:
                data['humidity'] = sensors['bme'].humidity
                data['pressure'] = sensors['bme'].pressure
            except: pass
            
        if 'light' in sensors:
            try:
                data['lux'] = sensors['light'].lux
            except: pass

        # 4. Read Compass
        if 'compass' in sensors:
            data['heading'] = sensors['compass'].read_heading()

        # 5. Check Motion
        if 'mpu' in sensors:
            try:
                accel = sensors['mpu'].acceleration
                if last_accel:
                    delta = math.sqrt(sum((a-b)**2 for a, b in zip(accel, last_accel)))
                    if delta > TAMPER_THRESHOLD_G:
                        buzz(0.1, 3) # fast alarm
                        send_matrix_alert(f"🏃‍♂️ MOVEMENT DETECTED! Delta: {delta:.2f}g")
                last_accel = accel
            except: pass

        # Check Thresholds (New)
        check_sensor_thresholds(data)

        # Logging
        msg = (f"Sol: {data['solar_watts']:.1f}W | Sys: {data['system_watts']:.1f}W | "
               f"Net: {data['net_watts']:.1f}W | {data['temperature']:.1f}°C | "
               f"Lid: {is_open} | {data['heading']:.0f}° | {data['lux']:.1f} lx")
        logger.info(msg)

        write_to_influx(data)

        # Shutdown Logic
        current_voltage = data['system_volts']
        if 0.5 < current_voltage < SHUTDOWN_VOLTAGE:
            low_voltage_counter += 1
            if low_voltage_counter >= SHUTDOWN_GRACE_PERIOD_SAMPLES:
                buzz(1.0) # Shutdown tone
                send_matrix_alert(f"🔴 CRITICAL LOW VOLTAGE ({current_voltage:.2f}V). Shutting down.")
                time.sleep(2)
                os.system("shutdown -h now")
        else:
            low_voltage_counter = 0

        # CSV Log
        try: log_to_csv(data)
        except: pass

        try: log_to_csv(data)
        except: pass

        time.sleep(current_sample_interval)

if __name__ == "__main__":
    main()
