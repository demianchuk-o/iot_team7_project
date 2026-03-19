from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Set, Dict, Any
import json
from database import SessionLocal
from models import ProcessedAgentData, ProcessedAgentDataInDB
import crud

router = APIRouter()

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
