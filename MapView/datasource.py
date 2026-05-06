import asyncio
import json
import threading

import websockets

from config import STORE_HOST, STORE_PORT


class Datasource:
    """
    WebSocket-клієнт до Store API. Зберігає накопичені точки у внутрішній черзі,
    UI забирає їх через get_new_points().
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.connection_status = "Disconnected"
        self._new_points = []
        self._lock = threading.Lock()

    def get_new_points(self, max_points: int = 5):
        """FIFO: до max_points найстаріших точок, решта лишається в черзі."""
        with self._lock:
            points = self._new_points[:max_points]
            self._new_points = self._new_points[max_points:]
        return points

    async def connect_to_server(self):
        uri = f"ws://{STORE_HOST}:{STORE_PORT}/sensors/ws/{self.user_id}"
        print(f"DEBUG: Connecting to {uri}")
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    self.connection_status = "Connected"
                    print("DEBUG: WebSocket Connected")
                    while True:
                        data = await websocket.recv()
                        self.handle_received_data(data)
            except Exception as e:
                self.connection_status = "Disconnected"
                print(f"DEBUG: Connection failed/closed: {e}. Retrying in 5s...")
                await asyncio.sleep(5)

    def handle_received_data(self, data):
        try:
            parsed = json.loads(data)
            records = [parsed] if isinstance(parsed, dict) else parsed
            with self._lock:
                self._new_points.extend(records)
                if len(self._new_points) > 1000:
                    self._new_points = self._new_points[-1000:]
        except Exception as e:
            print(f"DEBUG: Error handling data: {e} | Raw: {str(data)[:100]}...")
