import os
import time
import asyncio
import yaml
import logging
import meshtastic.serial_interface
from meshtastic import mesh_pb2
from nio import AsyncClient, MatrixRoom, RoomMessageText
import subprocess

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MeshtasticBridge")

# Configuration Path
CONFIG_PATH = os.environ.get("BRIDGE_CONFIG", "/etc/meshtastic-bridge/config.yaml")

class MeshtasticMatrixBridge:
    def __init__(self, config):
        self.config = config
        self.matrix_client = None
        self.mesh_interface = None
        self.room_id = config['matrix']['room_id']

    async def start_matrix(self):
        logger.info(f"Connecting to Matrix Homeserver: {self.config['matrix']['homeserver']}")
        self.matrix_client = AsyncClient(
            self.config['matrix']['homeserver'],
            self.config['matrix']['user_id']
        )
        self.matrix_client.access_token = self.config['matrix']['access_token']
        
        # Verify connection
        whoami = await self.matrix_client.whoami()
        logger.info(f"Matrix Connected as: {whoami}")

        # Join Room
        await self.matrix_client.join(self.room_id)
        logger.info(f"Joined Room: {self.room_id}")

        # Start Sync Loop to receive commands
        self.matrix_client.add_event_callback(self.on_matrix_message, RoomMessageText)
        asyncio.create_task(self.matrix_client.sync_forever(timeout=30000))

    def start_meshtastic(self):
        logger.info("Connecting to Meshtastic Node...")
        meshtastic_conf = self.config['meshtastic']
        connection_type = meshtastic_conf.get('connection_type', 'serial')

        if connection_type == 'network':
            host = meshtastic_conf['network']['host']
            port = meshtastic_conf['network'].get('port', 4403)
            import meshtastic.tcp_interface
            self.mesh_interface = meshtastic.tcp_interface.TCPInterface(host, port)
            logger.info(f"Connected to Meshtastic via TCP: {host}:{port}")
        else:
            # Fallback to serial
            serial_config = meshtastic_conf.get('serial', {})
            port = serial_config.get('port', '/dev/ttyUSB0')
            self.mesh_interface = meshtastic.serial_interface.SerialInterface(devPath=port)
            logger.info(f"Connected to Meshtastic via Serial: {port}")
        
        # Subscribe to messages
        from pubsub import pub
        pub.subscribe(self.on_meshtastic_message, "meshtastic.receive")

    async def on_matrix_message(self, room: MatrixRoom, event: RoomMessageText):
        if room.room_id != self.room_id:
            return

        body = event.body.strip()
        sender = event.sender
        logger.info(f"Matrix Message received from {sender}: {body}")
        
        # Matrix Auth Check
        allowed_users = self.config.get('security', {}).get('allowed_matrix_users', [])
        if allowed_users and sender not in allowed_users:
            logger.warning(f"Unauthorized Matrix command attempt from {sender}")
            return

        await self.process_command(body, "Matrix")

    def on_meshtastic_message(self, packet, interface):
        try:
            if 'decoded' in packet:
                decoded = packet['decoded']
                if decoded.get('portnum') == 'TEXT_MESSAGE_APP':
                    text_content = decoded.get('text', '')
                    sender = packet.get('fromId', 'Unknown')
                    
                    if text_content:
                        logger.info(f"Received from Mesh: {sender}: {text_content}")
                        
                        # Process Command
                        if text_content.startswith("!"):
                            asyncio.run_coroutine_threadsafe(
                                self.process_command_lora(text_content, sender),
                                self.loop
                            )

                        # Forward to Matrix
                        asyncio.run_coroutine_threadsafe(
                             self.send_to_matrix(f"**[{sender}]**: {text_content}"),
                             self.loop
                        )
        except Exception as e:
            logger.error(f"Error processing packet: {e}")

    async def process_command_lora(self, text, sender):
        # LoRa Auth Check (PIN)
        pin = self.config.get('security', {}).get('admin_pin')
        
        if not pin:
             # No PIN configured -> Locked by default or Insecure? Let's default to requiring PIN if sec section exists
             logger.warning("LoRa command ignored: No admin_pin configured.")
             return

        # Expect format: !<PIN> <CMD>  e.g., !1234 wifi on
        parts = text.split(' ', 1)
        if len(parts) < 2:
            return # Malformed

        cmd_pin_part = parts[0] # "!1234"
        command_body = "!" + parts[1] # "!wifi on"

        if cmd_pin_part == f"!{pin}":
            logger.info(f"LoRa Auth Success for {sender}")
            await self.process_command(command_body, f"Mesh User {sender}")
        else:
            logger.warning(f"LoRa Auth Failed for {sender}. Invalid PIN.")

    async def process_command(self, body, source):
        cmd = body.lower()
        if not cmd.startswith("!"):
            return

        logger.info(f"Processing command from {source}: {cmd}")

        if cmd == "!lte on":
            await self.toggle_interface(self.config.get('lte_interface', 'wwan0'), True, "LTE")
        elif cmd == "!lte off":
            await self.toggle_interface(self.config.get('lte_interface', 'wwan0'), False, "LTE")
            
        elif cmd == "!wifi on":
            await self.toggle_interface(self.config.get('wifi_interface', 'wlan1'), True, "High-Power WiFi")
        elif cmd == "!wifi off":
            await self.toggle_interface(self.config.get('wifi_interface', 'wlan1'), False, "High-Power WiFi")
            
        elif cmd == "!eco on":
            await self.send_to_matrix("🍃 Activating ECO Mode (Disabling LTE & High-Power WiFi)...")
            await self.toggle_interface(self.config.get('lte_interface', 'wwan0'), False, "LTE")
            await self.toggle_interface(self.config.get('wifi_interface', 'wlan1'), False, "High-Power WiFi")
            
        elif cmd == "!status":
             await self.report_status()

    async def toggle_interface(self, interface, state, label):
        action = "up" if state else "down"
        try:
            logger.info(f"Toggling {label} ({interface}) {action}...")
            result = subprocess.run(["ip", "link", "set", interface, action], capture_output=True, text=True)
            
            if result.returncode == 0:
                await self.send_to_matrix(f"✅ {label} turned **{action.upper()}**.")
            else:
                await self.send_to_matrix(f"⚠️ Failed to toggle {label}: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to toggle {label}: {e}")
            await self.send_to_matrix(f"🛑 Error controlling {label}: {str(e)}")

    async def report_status(self):
        try:
            # Check Interface States
            lte_iface = self.config.get('lte_interface', 'wwan0')
            wifi_iface = self.config.get('wifi_interface', 'wlan1')
            
            lte_state = "🟢 UP" if self.is_interface_up(lte_iface) else "🔴 DOWN"
            wifi_state = "🟢 UP" if self.is_interface_up(wifi_iface) else "🔴 DOWN"
            
            status_msg = (
                f"**System Status**:\n"
                f"📡 **LTE** ({lte_iface}): {lte_state}\n"
                f"📶 **WiFi** ({wifi_iface}): {wifi_state}"
            )
            await self.send_to_matrix(status_msg)
        except Exception as e:
            await self.send_to_matrix(f"Error getting status: {e}")

    def is_interface_up(self, interface):
        try:
            with open(f"/sys/class/net/{interface}/operstate", "r") as f:
                return "up" in f.read().strip().lower()
        except:
            return False

    async def run(self):
        self.loop = asyncio.get_running_loop()
        await self.start_matrix()
        # Meshtastic serial interface is blocking/threaded, so we start it here
        # It runs its own reader thread.
        self.start_meshtastic()
        
        # Keep the main loop alive
        while True:
            await asyncio.sleep(1)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        logger.error(f"Config file not found at {CONFIG_PATH}")
        return None
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    config = load_config()
    if config:
        bridge = MeshtasticMatrixBridge(config)
        try:
            asyncio.run(bridge.run())
        except KeyboardInterrupt:
            logger.info("Stopping Bridge...")
            if bridge.mesh_interface:
                bridge.mesh_interface.close()
            if bridge.matrix_client:
                asyncio.run(bridge.matrix_client.close())
