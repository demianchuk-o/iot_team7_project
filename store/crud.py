from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, update as sa_update, delete as sa_delete
from models import processed_agent_data, parking_data, traffic_light_data, ProcessedAgentData, ParkingData, TrafficLightData

def create_processed_agent_data(db: Session, data: List[ProcessedAgentData]):
    result = []
    for item in data:
        db_item = {
            "road_state": item.road_state,
            "user_id": item.agent_data.user_id,
            "x": item.agent_data.accelerometer.x,
            "y": item.agent_data.accelerometer.y,
            "z": item.agent_data.accelerometer.z,
            "latitude": item.agent_data.gps.latitude,
            "longitude": item.agent_data.gps.longitude,
            "timestamp": item.agent_data.timestamp,
        }
        query = processed_agent_data.insert().values(**db_item).returning(processed_agent_data.c.id)
        item_id = db.execute(query).fetchone()[0]
        db_item["id"] = item_id
        result.append(db_item)
    db.commit()
    return result

def get_processed_agent_data(db: Session, processed_agent_data_id: int):
    query = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
    row = db.execute(query).fetchone()
    return row._asdict() if row else None

def list_processed_agent_data(db: Session):
    query = select(processed_agent_data)
    rows = db.execute(query).fetchall()
    return [row._asdict() for row in rows]

def update_processed_agent_data(db: Session, processed_agent_data_id: int, data: ProcessedAgentData):
    db_item = {
        "road_state": data.road_state,
        "user_id": data.agent_data.user_id,
        "x": data.agent_data.accelerometer.x,
        "y": data.agent_data.accelerometer.y,
        "z": data.agent_data.accelerometer.z,
        "latitude": data.agent_data.gps.latitude,
        "longitude": data.agent_data.gps.longitude,
        "timestamp": data.agent_data.timestamp,
    }
    query = processed_agent_data.update().where(processed_agent_data.c.id == processed_agent_data_id).values(**db_item)
    result = db.execute(query)
    if result.rowcount == 0:
        return None
    db.commit()
    return {**db_item, "id": processed_agent_data_id}

def delete_processed_agent_data(db: Session, processed_agent_data_id: int):
    query_select = select(processed_agent_data).where(processed_agent_data.c.id == processed_agent_data_id)
    row = db.execute(query_select).fetchone()
    if not row:
        return None
    
    query_delete = processed_agent_data.delete().where(processed_agent_data.c.id == processed_agent_data_id)
    db.execute(query_delete)
    db.commit()
    return row._asdict()

# Parking data

def create_parking_data(db: Session, data: List[ParkingData]):
    values = []
    for item in data:
        values.append({
            "user_id": item.user_id,
            "parking_id": item.parking_id,
            "is_occupied": item.is_occupied,
            "total_spots": item.total_spots,
            "latitude": item.gps.latitude,
            "longitude": item.gps.longitude,
            "timestamp": item.timestamp
        })

    if values:
        result = db.execute(parking_data.insert().returning(*parking_data.c), values)
        db.commit()
        return [dict(row._mapping) for row in result]
    return []

def get_parking_data(db: Session, data_id: int):
    result = db.execute(select(parking_data).where(parking_data.c.id == data_id)).first()
    return dict(result._mapping) if result else None

def list_parking_data(db: Session):
    result = db.execute(select(parking_data)).all()
    return [dict(row._mapping) for row in result]

def update_parking_data(db: Session, data_id: int, data: ParkingData):
    stmt = (
        sa_update(parking_data)
        .where(parking_data.c.id == data_id)
        .values(
            user_id=data.user_id,
            parking_id=data.parking_id,
            is_occupied=data.is_occupied,
            total_spots=data.total_spots,
            latitude=data.gps.latitude,
            longitude=data.gps.longitude,
            timestamp=data.timestamp
        )
        .returning(*parking_data.c)
    )
    result = db.execute(stmt).first()
    db.commit()
    return dict(result._mapping) if result else None

def delete_parking_data(db: Session, data_id: int):
    stmt = sa_delete(parking_data).where(parking_data.c.id == data_id).returning(*parking_data.c)
    result = db.execute(stmt).first()
    db.commit()
    return dict(result._mapping) if result else None

# Traffic light

def create_traffic_light_data(db: Session, data: List[TrafficLightData]):
    values = []
    for item in data:
        values.append({
            "user_id": item.user_id,
            "light_id": item.light_id,
            "current_state": item.current_state,
            "car_count": item.car_count,
            "latitude": item.gps.latitude,
            "longitude": item.gps.longitude,
            "timestamp": item.timestamp
        })

    if values:
        result = db.execute(traffic_light_data.insert().returning(*traffic_light_data.c), values)
        db.commit()
        return [dict(row._mapping) for row in result]
    return []

def get_traffic_light_data(db: Session, data_id: int):
    result = db.execute(select(traffic_light_data).where(traffic_light_data.c.id == data_id)).first()
    return dict(result._mapping) if result else None

def list_traffic_light_data(db: Session):
    result = db.execute(select(traffic_light_data)).all()
    return [dict(row._mapping) for row in result]

def update_traffic_light_data(db: Session, data_id: int, data: TrafficLightData):
    stmt = (
        sa_update(traffic_light_data)
        .where(traffic_light_data.c.id == data_id)
        .values(
            user_id=data.user_id,
            light_id=data.light_id,
            current_state=data.current_state,
            car_count=data.car_count,
            latitude=data.gps.latitude,
            longitude=data.gps.longitude,
            timestamp=data.timestamp
        )
        .returning(*traffic_light_data.c)
    )
    result = db.execute(stmt).first()
    db.commit()
    return dict(result._mapping) if result else None

def delete_traffic_light_data(db: Session, data_id: int):
    stmt = sa_delete(traffic_light_data).where(traffic_light_data.c.id == data_id).returning(*traffic_light_data.c)
    result = db.execute(stmt).first()
    db.commit()
    return dict(result._mapping) if result else None