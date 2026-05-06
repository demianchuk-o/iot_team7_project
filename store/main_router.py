from typing import Any, Dict, List, Set

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

import crud
from database import SessionLocal
from models import SensorReadingInDB
from shared.sensor import SensorReading

router = APIRouter()

# WebSocket subscriptions: user_id -> set активних з'єднань
subscriptions: Dict[int, Set[WebSocket]] = {}


async def broadcast_to_subscribers(user_id: int, data: Any):
    """Розсилає JSON-повідомлення усім WebSocket-клієнтам user_id."""
    if user_id not in subscriptions:
        return
    dead: list[WebSocket] = []
    for ws in subscriptions[user_id]:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        subscriptions[user_id].discard(ws)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """MapView (та інші клієнти) тримають з'єднання тут і отримують push-оновлення."""
    await websocket.accept()
    subscriptions.setdefault(user_id, set()).add(websocket)
    try:
        while True:
            # Не очікуємо повідомлень від клієнта — тільки тримаємо з'єднання
            await websocket.receive_text()
    except WebSocketDisconnect:
        subscriptions[user_id].discard(websocket)


@router.post("/", response_model=List[SensorReadingInDB])
async def create_sensor_batch(batch: List[SensorReading]):
    """Універсальний endpoint для будь-якого типу сенсора."""
    with SessionLocal() as db:
        result = crud.create_sensor_readings(db, batch)
        for item in result:
            payload = {
                **item,
                "timestamp": item["timestamp"].isoformat(),
            }
            await broadcast_to_subscribers(item["user_id"], payload)
        return result


@router.get("/", response_model=List[SensorReadingInDB])
def list_all(limit: int = 100):
    with SessionLocal() as db:
        return crud.list_all(db, limit)


@router.get("/{sensor_type}/", response_model=List[SensorReadingInDB])
def list_by_type(sensor_type: str, limit: int = 100):
    with SessionLocal() as db:
        return crud.list_by_type(db, sensor_type, limit)


@router.get("/{sensor_type}/latest/", response_model=List[SensorReadingInDB])
def latest_per_object(sensor_type: str):
    with SessionLocal() as db:
        return crud.get_latest_per_object(db, sensor_type)


@router.get("/by_id/{reading_id}", response_model=SensorReadingInDB)
def get_by_id(reading_id: int):
    with SessionLocal() as db:
        data = crud.get_sensor_reading(db, reading_id)
        if not data:
            raise HTTPException(status_code=404, detail="Reading not found")
        return data
