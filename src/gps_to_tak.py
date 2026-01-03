#!/usr/bin/env python3
import socket
import time
import uuid
import os
import json
import logging
from gps3 import gps3
from datetime import datetime, timezone

# --- Config ---
TAK_IP = os.getenv("TAK_IP", "239.2.3.1") # Multicast Default
TAK_PORT = int(os.getenv("TAK_PORT", "6969"))
GPSD_HOST = os.getenv("GPSD_HOST", "127.0.0.1")
GPSD_PORT = int(os.getenv("GPSD_PORT", "2947"))
CALLSIGN = os.getenv("TAK_CALLSIGN", "LE_REDUIT")
UUID = os.getenv("TAK_UUID", f"reduit-{uuid.getnode()}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - TAK - %(message)s')
logger = logging.getLogger("tak_bridge")

def get_iso_time():
    # CoT requires ISO 8601 UTC
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def build_cot_xml(lat, lon, hae, speed, course):
    # Basic PLI (Position Location Information) CoT
    now = get_iso_time()
    # Stale in 2 minutes
    stale_time = (datetime.now(timezone.utc).timestamp() + 120)
    stale_iso = datetime.fromtimestamp(stale_time, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    # a-f-G-E-V-C: Friendly - Ground - Equipment - Vehicle - Civilian (Example)
    # a-u-G: Unknown Ground (Default if unsure)
    # Let's use Friendly Ground Unit
    type_str = "a-f-G-U-C" 
    
    # Read Telemetry from Power Monitor
    remarks = "Le Reduit: Online"
    try:
        if os.path.exists("/tmp/reduit_status.json"):
            with open("/tmp/reduit_status.json", "r") as f:
                d = json.load(f)
                remarks = (f"🔋 {d.get('system_volts',0):.1f}V {d.get('net_watts',0):.0f}W | "
                           f"🌡️ {d.get('temperature',0):.0f}C | "
                           f"💡 {d.get('lux',0):.0f}lx | "
                           f"{'🔓 OPEN' if d.get('lid_open') else '🔒'}")
    except: pass

    xml = f"""<?xml version='1.0' standalone='yes'?>
<event version="2.0" uid="{UUID}" type="{type_str}" time="{now}" start="{now}" stale="{stale_iso}" how="m-g">
    <point lat="{lat}" lon="{lon}" hae="{hae}" ce="9999999" le="9999999"/>
    <detail>
        <contact callsign="{CALLSIGN}"/>
        <track course="{course}" speed="{speed}"/>
        <remarks>{remarks}</remarks>
    </detail>
</event>"""
    return xml.encode('utf-8')

def main():
    logger.info(f"Starting TAK GPS Bridge. Sending to {TAK_IP}:{TAK_PORT}")
    
    # Setup UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    
    # Setup GPSD Client
    gps_socket = gps3.GPSDSocket()
    data_stream = gps3.DataStream()
    
    try:
        gps_socket.connect(host=GPSD_HOST, port=GPSD_PORT)
        gps_socket.watch()
        
        for new_data in gps_socket:
            if new_data:
                data_stream.unpack(new_data)
                
                # Check for TPV (Time Position Velocity) data
                if data_stream.TPV['lat'] != 'n/a':
                    lat = float(data_stream.TPV['lat'])
                    lon = float(data_stream.TPV['lon'])
                    alt = float(data_stream.TPV['alt']) if data_stream.TPV['alt'] != 'n/a' else 0.0
                    speed = float(data_stream.TPV['speed']) if data_stream.TPV['speed'] != 'n/a' else 0.0
                    track = float(data_stream.TPV['track']) if data_stream.TPV['track'] != 'n/a' else 0.0
                    
                    xml_payload = build_cot_xml(lat, lon, alt, speed, track)
                    
                    try:
                        sock.sendto(xml_payload, (TAK_IP, TAK_PORT))
                        logger.debug(f"Sent CoT: {lat}, {lon}")
                    except Exception as e:
                        logger.error(f"Send failed: {e}")
                        
            time.sleep(1) # Rate limit? GPSD usually sends 1Hz
            
    except Exception as e:
        logger.error(f"GPSD Error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()
