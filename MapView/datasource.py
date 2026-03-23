import asyncio
import json
from datetime import datetime
import websockets
from pydantic import BaseModel, field_validator
from config import STORE_HOST, STORE_PORT

# Pydantic models
class ProcessedAgentData(BaseModel):
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def check_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid timestamp format. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."
            )


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
            # The data coming from send_json is already a dict (deserialized by send_json)
            # OR a single JSON string. Let's handle both.
            parsed = json.loads(data)
            
            # If it's a single object (which send_data_to_subscribers seems to do)
            if isinstance(parsed, dict):
                records = [parsed]
            else:
                records = parsed

            processed_agent_data_list = sorted(
                [ProcessedAgentData(**item) for item in records],
                key=lambda v: v.timestamp,
            )
            new_points = [
                (
                    processed_agent_data.longitude,  # Swapped: latitude is in longitude field in gps.csv
                    processed_agent_data.latitude,   # Swapped: longitude is in latitude field in gps.csv
                    processed_agent_data.road_state,
                )
                for processed_agent_data in processed_agent_data_list
            ]
            self._new_points.extend(new_points)
        except Exception as e:
            print(f"DEBUG: Error handling data: {e} | Raw data: {data[:100]}...")
