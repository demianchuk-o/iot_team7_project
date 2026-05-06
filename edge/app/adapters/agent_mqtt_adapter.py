import logging

import paho.mqtt.client as mqtt

from app.interfaces.agent_gateway import AgentGateway
from app.interfaces.hub_gateway import HubGateway
from app.usecases.data_processing import process_sensor_reading
from shared.sensor import SensorReading


class AgentMQTTAdapter(AgentGateway):
    def __init__(self, broker_host: str, broker_port: int, hub_gateway: HubGateway):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.hub_gateway = hub_gateway

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Edge: connected to MQTT broker")
            client.subscribe("sensors/+/raw")
        else:
            logging.error(f"Edge: failed to connect to MQTT, rc={rc}")

    def on_message(self, client, userdata, msg):
        try:
            parts = msg.topic.split("/")
            if len(parts) != 3 or parts[0] != "sensors" or parts[2] != "raw":
                return
            sensor_type = parts[1]

            reading = SensorReading.model_validate_json(
                msg.payload.decode("utf-8")
            )
            processed = process_sensor_reading(reading)

            target = f"sensors/{sensor_type}/processed"
            if not self.hub_gateway.save_data(processed, topic=target):
                logging.error(f"Edge: failed to forward to {target}")
        except Exception as e:
            logging.error(f"Edge: error processing message from {msg.topic}: {e}")

    def connect(self):
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_host, self.broker_port, 60)

    def start(self):
        self.loop_forever()

    def loop_forever(self):
        self.client.loop_forever()

    def stop(self):
        self.client.loop_stop()
