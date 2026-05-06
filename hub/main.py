import logging
from typing import List

from fastapi import FastAPI
from redis import Redis
import paho.mqtt.client as mqtt

from app.adapters.store_api_adapter import StoreApiAdapter
from config import (
    STORE_API_BASE_URL,
    REDIS_HOST,
    REDIS_PORT,
    BATCH_SIZE,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
)
from shared.sensor import SensorReading

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log"),
    ],
)

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)
store_adapter = StoreApiAdapter(api_base_url=STORE_API_BASE_URL)
app = FastAPI(title="RoadVision Hub")
client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker")
        client.subscribe("sensors/+/raw")
        client.subscribe("sensors/+/processed")
    else:
        logging.error(f"Failed to connect to MQTT broker, rc={rc}")


def _flush_if_ready(queue: str) -> None:
    """Якщо черга набрала BATCH_SIZE — забрати батч і відправити в Store."""
    if redis_client.llen(queue) < BATCH_SIZE:
        return

    batch: List[SensorReading] = []
    for _ in range(BATCH_SIZE):
        data_json = redis_client.rpop(queue)
        if data_json:
            try:
                batch.append(SensorReading.model_validate_json(data_json))
            except Exception as e:
                logging.error(f"Failed to parse from {queue}: {e}")

    if batch:
        store_adapter.save_sensor_batch(batch)


def on_message(client, userdata, msg):
    """Універсальний обробник — формат топіка: sensors/{type}/{stage}."""
    try:
        parts = msg.topic.split("/")
        if len(parts) != 3 or parts[0] != "sensors":
            logging.warning(f"Unknown topic format: {msg.topic}")
            return
        sensor_type = parts[1]

        reading = SensorReading.model_validate_json(msg.payload.decode("utf-8"))

        if reading.payload.sensor_type != sensor_type:
            logging.error(
                f"Topic/payload mismatch: topic={sensor_type}, "
                f"payload={reading.payload.sensor_type}"
            )
            return

        queue = f"sensor_queue:{sensor_type}"
        redis_client.lpush(queue, reading.model_dump_json())
        redis_client.ltrim(queue, 0, 9999)

        _flush_if_ready(queue)

    except Exception as e:
        logging.error(f"Error in on_message ({msg.topic}): {e}")


client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
client.loop_start()
