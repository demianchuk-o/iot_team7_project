from typing import List

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from models import sensor_readings
from shared.sensor import SensorReading


def create_sensor_readings(db: Session, batch: List[SensorReading]):
    """Bulk-insert батчу показань."""
    if not batch:
        return []

    values = [
        {
            "sensor_type": r.payload.sensor_type,
            "sensor_id": r.sensor_id,
            "user_id": r.user_id,
            "latitude": r.gps.latitude,
            "longitude": r.gps.longitude,
            "timestamp": r.timestamp,
            "payload": r.payload.model_dump(),
        }
        for r in batch
    ]
    result = db.execute(
        sensor_readings.insert().returning(*sensor_readings.c),
        values,
    )
    db.commit()
    return [dict(row._mapping) for row in result]


def get_sensor_reading(db: Session, reading_id: int):
    query = select(sensor_readings).where(sensor_readings.c.id == reading_id)
    row = db.execute(query).fetchone()
    return dict(row._mapping) if row else None


def list_by_type(db: Session, sensor_type: str, limit: int = 100):
    """Останні N показань заданого типу, від найновіших."""
    query = (
        select(sensor_readings)
        .where(sensor_readings.c.sensor_type == sensor_type)
        .order_by(sensor_readings.c.timestamp.desc())
        .limit(limit)
    )
    return [dict(r._mapping) for r in db.execute(query).all()]


def list_all(db: Session, limit: int = 100):
    """Останні N показань усіх типів."""
    query = (
        select(sensor_readings)
        .order_by(sensor_readings.c.timestamp.desc())
        .limit(limit)
    )
    return [dict(r._mapping) for r in db.execute(query).all()]


def get_latest_per_object(db: Session, sensor_type: str):
    """
    Найсвіжіше показання для КОЖНОГО унікального sensor_id даного типу.
    """
    query = text("""
        SELECT DISTINCT ON (sensor_id) *
        FROM sensor_readings
        WHERE sensor_type = :sensor_type
        ORDER BY sensor_id, timestamp DESC
    """)
    return [
        dict(r._mapping)
        for r in db.execute(query, {"sensor_type": sensor_type}).all()
    ]
