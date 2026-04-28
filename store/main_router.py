from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Set, Dict, Any
import json
from database import SessionLocal
# from models import ProcessedAgentData, ProcessedAgentDataInDB
from models import (
ProcessedAgentData, ProcessedAgentDataInDB,
    ParkingData, ParkingDataInDB,
    TrafficLightData, TrafficLightDataInDB
)
import crud

router = APIRouter()

parking_router = APIRouter(prefix="/parking", tags=["Parking"])
traffic_light_router = APIRouter(prefix="/traffic_light", tags=["Traffic Light"])

# WebSocket subscriptions
subscriptions: Dict[int, Set[WebSocket]] = {}

async def send_data_to_subscribers(user_id: int, data: Any):
    if user_id in subscriptions:
        for websocket in subscriptions[user_id]:
            await websocket.send_json(data)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    if user_id not in subscriptions:
        subscriptions[user_id] = set()
    subscriptions[user_id].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions[user_id].remove(websocket)

@router.post("/", response_model=List[ProcessedAgentDataInDB])
async def create_processed_agent_data(data: List[ProcessedAgentData]):
    with SessionLocal() as db:
        result = crud.create_processed_agent_data(db, data)
        for item in result:
            serializable_item = item.copy()
            serializable_item["timestamp"] = serializable_item["timestamp"].isoformat()
            await send_data_to_subscribers(item["user_id"], serializable_item)
        return result

@router.get("/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def read_processed_agent_data(processed_agent_data_id: int):
    with SessionLocal() as db:
        data = crud.get_processed_agent_data(db, processed_agent_data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        return data

@router.get("/", response_model=List[ProcessedAgentDataInDB])
def list_processed_agent_data():
    with SessionLocal() as db:
        return crud.list_processed_agent_data(db)

@router.put("/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def update_processed_agent_data(processed_agent_data_id: int, data: ProcessedAgentData):
    with SessionLocal() as db:
        updated_data = crud.update_processed_agent_data(db, processed_agent_data_id, data)
        if not updated_data:
            raise HTTPException(status_code=404, detail="Data not found")
        return updated_data

@router.delete("/{processed_agent_data_id}", response_model=ProcessedAgentDataInDB)
def delete_processed_agent_data(processed_agent_data_id: int):
    with SessionLocal() as db:
        deleted_data = crud.delete_processed_agent_data(db, processed_agent_data_id)
        if not deleted_data:
            raise HTTPException(status_code=404, detail="Data not found")
        return deleted_data

# Parking data
@parking_router.post("/", response_model=List[ParkingDataInDB])
async def create_parking_batch(data: List[ParkingData]):
    with SessionLocal() as db:
        result = crud.create_parking_data(db, data)
        for item in result:
            serializable_item = item.copy()
            serializable_item["timestamp"] = serializable_item["timestamp"].isoformat()
            serializable_item["data_type"] = "parking"
            await send_data_to_subscribers(item["user_id"], serializable_item)
        return result

@parking_router.get("/{data_id}", response_model=ParkingDataInDB)
def read_parking_data(data_id: int):
    with SessionLocal() as db:
        data = crud.get_parking_data(db, data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Parking data not found")
        return data

@parking_router.get("/", response_model=List[ParkingDataInDB])
def get_all_parking_data():
    with SessionLocal() as db:
        return crud.list_parking_data(db)

@parking_router.put("/{data_id}", response_model=ParkingDataInDB)
def update_parking_data(data_id: int, data: ParkingData):
    with SessionLocal() as db:
        updated_data = crud.update_parking_data(db, data_id, data)
        if not updated_data:
            raise HTTPException(status_code=404, detail="Parking data not found")
        return updated_data

@parking_router.delete("/{data_id}", response_model=ParkingDataInDB)
def delete_parking_data(data_id: int):
    with SessionLocal() as db:
        deleted_data = crud.delete_parking_data(db, data_id)
        if not deleted_data:
            raise HTTPException(status_code=404, detail="Parking data not found")
        return deleted_data

# Traffic light data
@traffic_light_router.post("/", response_model=List[TrafficLightDataInDB])
async def create_traffic_light_batch(data: List[TrafficLightData]):
    with SessionLocal() as db:
        result = crud.create_traffic_light_data(db, data)
        for item in result:
            serializable_item = item.copy()
            serializable_item["timestamp"] = serializable_item["timestamp"].isoformat()
            serializable_item["data_type"] = "traffic_light"
            await send_data_to_subscribers(item["user_id"], serializable_item)
        return result

@traffic_light_router.get("/{data_id}", response_model=TrafficLightDataInDB)
def read_traffic_light_data(data_id: int):
    with SessionLocal() as db:
        data = crud.get_traffic_light_data(db, data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Traffic light data not found")
        return data

@traffic_light_router.get("/", response_model=List[TrafficLightDataInDB])
def get_all_traffic_light_data():
    with SessionLocal() as db:
        return crud.list_traffic_light_data(db)

@traffic_light_router.put("/{data_id}", response_model=TrafficLightDataInDB)
def update_traffic_light_data(data_id: int, data: TrafficLightData):
    with SessionLocal() as db:
        updated_data = crud.update_traffic_light_data(db, data_id, data)
        if not updated_data:
            raise HTTPException(status_code=404, detail="Traffic light data not found")
        return updated_data

@traffic_light_router.delete("/{data_id}", response_model=TrafficLightDataInDB)
def delete_traffic_light_data(data_id: int):
    with SessionLocal() as db:
        deleted_data = crud.delete_traffic_light_data(db, data_id)
        if not deleted_data:
            raise HTTPException(status_code=404, detail="Traffic light data not found")
        return deleted_data