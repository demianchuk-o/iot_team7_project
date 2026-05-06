from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator

# === Спільні підтипи ===

class GpsData(BaseModel):
    latitude: float
    longitude: float


class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float


# === Payloads — по одному на тип сенсора ===

class RoadPayload(BaseModel):
    sensor_type: Literal["road"] = "road"
    accelerometer: AccelerometerData
    road_state: str | None = None


class ParkingPayload(BaseModel):
    sensor_type: Literal["parking"] = "parking"
    is_occupied: bool
    total_spots: int


class TrafficLightPayload(BaseModel):
    sensor_type: Literal["traffic_light"] = "traffic_light"
    current_state: str  # red / yellow / green
    car_count: int


class NetworkPayload(BaseModel):
    sensor_type: Literal["network"] = "network"
    latency_ms: float
    packet_loss_pct: float
    throughput_kbps: float
    rssi_dbm: float
    anomaly_score: float | None = None
    network_state: str | None = None


SensorPayload = Annotated[
    Union[RoadPayload, ParkingPayload, TrafficLightPayload, NetworkPayload],
    Field(discriminator="sensor_type"),
]

class SensorReading(BaseModel):
    sensor_id: str       # "tl_42", "park_15", "car_001"
    user_id: int
    gps: GpsData
    timestamp: datetime
    payload: SensorPayload

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid timestamp format. Expected ISO 8601 (YYYY-MM-DDTHH:MM:SS)."
            )
