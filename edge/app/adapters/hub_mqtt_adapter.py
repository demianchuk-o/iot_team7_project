import logging

from paho.mqtt import client as mqtt_client

from app.interfaces.hub_gateway import HubGateway
from shared.sensor import SensorReading


class HubMqttAdapter(HubGateway):
    """Публікація обробленого SensorReading в Hub через MQTT."""

    def __init__(self, broker: str, port: int):
        self.broker = broker
        self.port = port
        self.mqtt_client = self._connect_mqtt(broker, port)

    def save_data(self, reading: SensorReading, topic: str) -> bool:
        """Публікація reading в указаний топік (тип визначає Edge)."""
        try:
            msg = reading.model_dump_json()
            result = self.mqtt_client.publish(topic, msg)
            if result[0] == 0:
                return True
            logging.error(
                f"HubMqttAdapter: publish to {topic} failed, status={result[0]}"
            )
            return False
        except Exception as e:
            logging.error(f"HubMqttAdapter.save_data: {e}")
            return False

    @staticmethod
    def _connect_mqtt(broker: str, port: int) -> mqtt_client.Client:
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logging.info(f"Edge->Hub MQTT connected ({broker}:{port})")
            else:
                logging.error(f"Edge->Hub MQTT connection failed, rc={rc}")

        client = mqtt_client.Client()
        client.on_connect = on_connect
        client.connect(broker, port)
        client.loop_start()
        return client
