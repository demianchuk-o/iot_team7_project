from datetime import datetime
from pydantic import BaseModel, field_validator

class GpsData(BaseModel):
    latitude: float
    longitude: float

class ParkingData(BaseModel):
    user_id: int
    parking_id: str
    is_occupied: bool
    total_spots: int
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