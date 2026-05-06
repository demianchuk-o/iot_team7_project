from datetime import datetime
from typing import Any

from sqlalchemy import (
    MetaData, Table, Column,
    Integer, String, Float, DateTime,
)
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel


# === SQLAlchemy ===

metadata = MetaData()

sensor_readings = Table(
    "sensor_readings",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("sensor_type", String, index=True),
    Column("sensor_id", String, index=True),
    Column("user_id", Integer, index=True),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("timestamp", DateTime, index=True),
    Column("payload", JSONB),
)


# === Pydantic для відповідей API ===

class SensorReadingInDB(BaseModel):
    id: int
    sensor_type: str
    sensor_id: str
    user_id: int
    latitude: float
    longitude: float
    timestamp: datetime
    payload: dict[str, Any]
