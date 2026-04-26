import asyncio
import json
import websockets
from config import STORE_HOST, STORE_PORT

class Datasource:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.connection_status = "Disconnected"
        self._new_points = []

    def get_new_points(self):
        points = self._new_points.copy()
        self._new_points = []
        return points

    async def connect_to_server(self):
        uri = f"ws://{STORE_HOST}:{STORE_PORT}/processed_agent_data/ws/{self.user_id}"
        print(f"DEBUG: Connecting to {uri}")
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.connection_status = "Connected"
                    print("DEBUG: WebSocket Connected")
                    while True:
                        data = await websocket.recv()
                        # print(f"DEBUG: Received raw data: {data}")
                        self.handle_received_data(data)
            except Exception as e:
                self.connection_status = "Disconnected"
                print(f"DEBUG: Connection failed/closed: {e}. Retrying in 5s...")
                await asyncio.sleep(5)

    def handle_received_data(self, data):
        try:
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                records = [parsed]
            else:
                records = parsed
            for item in records:
                # Determining data type
                data_type = item.get("data_type", "road")
                # Old logic with swapping coords data for roads
                if data_type == "road":
                    old_lat = item.get("latitude")
                    old_lon = item.get("longitude")
                    item["latitude"] = old_lon
                    item["longitude"] = old_lat
                self._new_points.append(item)
        except Exception as e:
            print(f"DEBUG: Error handling data: {e} | Raw data: {data[:100]}...")
