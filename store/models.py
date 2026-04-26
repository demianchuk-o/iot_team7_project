from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
)
from pydantic import BaseModel, field_validator
from datetime import datetime

metadata = MetaData()

# Define the ProcessedAgentData table
processed_agent_data = Table(
    "processed_agent_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("road_state", String),
    Column("user_id", Integer),
    Column("x", Float),
    Column("y", Float),
    Column("z", Float),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)

parking_data = Table(
    "parking_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer),
    Column("parking_id", String),
    Column("is_occupied", Boolean),
    Column("total_spots", Integer),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)

traffic_light_data = Table(
    "traffic_light_data",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer),
    Column("light_id", String),
    Column("current_state", String),
    Column("car_count", Integer),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime),
)

# SQLAlchemy model for response
class ProcessedAgentDataInDB(BaseModel):
    id: int
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime

class ParkingDataInDB(BaseModel):
    id: int
    user_id: int
    parking_id: str
    is_occupied: bool
    total_spots: int
    latitude: float
    longitude: float
    timestamp: datetime

class TrafficLightDataInDB(BaseModel):
    id: int
    user_id: int
    light_id: str
    current_state: str
    car_count: int
    latitude: float
    longitude: float
    timestamp: datetime

# FastAPI models for requests
class AccelerometerData(BaseModel):
    x: float
    y: float
    z: float

class GpsData(BaseModel):
    latitude: float
    longitude: float

def validate_timestamp(value):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(
            "Invalid timestamp format. Expected ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."
        )

class AgentData(BaseModel):
    user_id: int
    accelerometer: AccelerometerData
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def check_timestamp(cls, value):
        return validate_timestamp(value)

class ProcessedAgentData(BaseModel):
    road_state: str
    agent_data: AgentData

class ParkingData(BaseModel):
    user_id: int
    parking_id: str
    is_occupied: bool
    total_spots: int
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def check_timestamp(cls, value):
        return validate_timestamp(value)

class TrafficLightData(BaseModel):
    user_id: int
    light_id: str
    current_state: str  # Наприклад: "red", "yellow", "green"
    car_count: int
    gps: GpsData
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def check_timestamp(cls, value):
        return validate_timestamp(value)