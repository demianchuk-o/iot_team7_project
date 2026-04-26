import json
import logging
from typing import List

from fastapi import FastAPI
from redis import Redis
import paho.mqtt.client as mqtt

from app.adapters.store_api_adapter import StoreApiAdapter
from app.entities.processed_agent_data import ProcessedAgentData
from app.entities.parking_data import ParkingData
from app.entities.traffic_light_data import TrafficLightData
from config import (
    STORE_API_BASE_URL,
    REDIS_HOST,
    REDIS_PORT,
    BATCH_SIZE,
    MQTT_TOPIC,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
)

# Configure logging settings
logging.basicConfig(
    level=logging.INFO,  # Set the log level to INFO (you can use logging.DEBUG for more detailed logs)
    format="[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Output log messages to the console
        logging.FileHandler("app.log"),  # Save log messages to a file
    ],
)
# Create an instance of the Redis using the configuration
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)
# Create an instance of the StoreApiAdapter using the configuration
store_adapter = StoreApiAdapter(api_base_url=STORE_API_BASE_URL)
# Create an instance of the AgentMQTTAdapter using the configuration

# FastAPI
app = FastAPI()


@app.post("/processed_agent_data/")
async def save_processed_agent_data(processed_agent_data: ProcessedAgentData):
    redis_client.lpush("processed_agent_data", processed_agent_data.model_dump_json())
    if redis_client.llen("processed_agent_data") >= BATCH_SIZE:
        processed_agent_data_batch: List[ProcessedAgentData] = []
        for _ in range(BATCH_SIZE):
            processed_agent_data = ProcessedAgentData.model_validate_json(
                redis_client.lpop("processed_agent_data")
            )
            processed_agent_data_batch.append(processed_agent_data)
        print(processed_agent_data_batch)
        store_adapter.save_data(processed_agent_data_batch=processed_agent_data_batch)
    return {"status": "ok"}


# MQTT
client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
        client.subscribe("agent/parking/data")
        client.subscribe("agent/traffic_light/data")
    else:
        logging.info(f"Failed to connect to MQTT broker with code: {rc}")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        topic = msg.topic

        # Road data
        if topic == MQTT_TOPIC:
            # Parse payload as ProcessedAgentData (sent by Edge)
            processed_data = ProcessedAgentData.model_validate_json(payload)
            logging.info(f"Received processed data from Edge: {processed_data.road_state}")
            redis_client.lpush("processed_agent_data", processed_data.model_dump_json())
            if redis_client.llen("processed_agent_data") >= BATCH_SIZE:
                processed_agent_data_batch: List[ProcessedAgentData] = []
                for _ in range(BATCH_SIZE):
                    data_json = redis_client.lpop("processed_agent_data")
                    if data_json:
                        processed_agent_data_batch.append(ProcessedAgentData.model_validate_json(data_json))
                if processed_agent_data_batch:
                    logging.info(f"Saving batch of {len(processed_agent_data_batch)} items to Store API")
                    store_adapter.save_data(processed_agent_data_batch=processed_agent_data_batch)
            return {"status": "ok"}

        # Parking data
        elif topic == "agent/parking/data":
            valid_data = ParkingData.model_validate_json(payload)
            redis_client.lpush("parking_queue", valid_data.model_dump_json())
            if redis_client.llen("parking_queue") >= BATCH_SIZE:
                batch = []
                for _ in range(BATCH_SIZE):
                    data_json = redis_client.lpop("parking_queue")
                    if data_json:
                        batch.append(json.loads(data_json))
                if batch:
                    store_adapter.save_parking_data(data_batch=batch)
                    logging.info(f"Hub sent batch of {len(batch)} parking items.")

        # Traffic light data
        elif topic == "agent/traffic_light/data":
            valid_data = TrafficLightData.model_validate_json(payload)
            redis_client.lpush("traffic_light_queue", valid_data.model_dump_json())
            if redis_client.llen("traffic_light_queue") >= BATCH_SIZE:
                batch = []
                for _ in range(BATCH_SIZE):
                    data_json = redis_client.lpop("traffic_light_queue")
                    if data_json:
                        batch.append(json.loads(data_json))
                if batch:
                    store_adapter.save_traffic_light_data(data_batch=batch)
                    logging.info(f"Hub sent batch of {len(batch)} traffic light items.")

    except Exception as e:
        logging.error(f"Error processing MQTT message from {msg.topic}: {e}")


# Connect
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)

# Start
client.loop_start()
