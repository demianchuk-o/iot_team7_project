from datetime import datetime
from pydantic import BaseModel, field_validator
from app.entities.parking_data import GpsData

class TrafficLightData(BaseModel):
    user_id: int
    light_id: str
    current_state: str
    car_count: int
    gps: GpsData
    timestamp: datetime

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError("Invalid timestamp format.")