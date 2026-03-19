from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from models import processed_agent_data, ProcessedAgentData

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
