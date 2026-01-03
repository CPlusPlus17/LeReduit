import os
import time
import asyncio
import yaml
import logging
import meshtastic.serial_interface
from meshtastic import mesh_pb2
from nio import AsyncClient, MatrixRoom, RoomMessageText

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

        # Start Sync Loop in background if we want to receive matrix messages
        # For now, simplistic implementation: Just send Meshtastic -> Matrix
        # self.matrix_client.add_event_callback(self.on_matrix_message, RoomMessageText)
        # asyncio.create_task(self.matrix_client.sync_forever(timeout=30000))

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

    def on_meshtastic_message(self, packet, interface):
        try:
            if 'decoded' in packet:
                decoded = packet['decoded']
                if decoded.get('portnum') == 'TEXT_MESSAGE_APP':
                    text_content = decoded.get('text', '')
                    sender = packet.get('fromId', 'Unknown')
                    
                    if text_content:
                        logger.info(f"Received from Mesh: {sender}: {text_content}")
                        asyncio.run_coroutine_threadsafe(
                            self.send_to_matrix(f"**[{sender}]**: {text_content}"),
                            self.loop
                        )
        except Exception as e:
            logger.error(f"Error processing packet: {e}")

    async def send_to_matrix(self, message):
        if self.matrix_client:
            await self.matrix_client.room_send(
                room_id=self.room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message
                }
            )

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
