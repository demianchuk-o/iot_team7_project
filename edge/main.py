import logging

from app.adapters.agent_mqtt_adapter import AgentMQTTAdapter
from app.adapters.hub_mqtt_adapter import HubMqttAdapter
from config import (
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    HUB_MQTT_BROKER_HOST,
    HUB_MQTT_BROKER_PORT,
)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [edge] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log"),
        ],
    )

    # Hub-адаптер тепер не приймає topic — топік визначається per-message
    # на основі типу сенсора (sensors/<type>/processed).
    hub_adapter = HubMqttAdapter(
        broker=HUB_MQTT_BROKER_HOST,
        port=HUB_MQTT_BROKER_PORT,
    )
    agent_adapter = AgentMQTTAdapter(
        broker_host=MQTT_BROKER_HOST,
        broker_port=MQTT_BROKER_PORT,
        hub_gateway=hub_adapter,
    )

    try:
        agent_adapter.connect()
        agent_adapter.loop_forever()
    except KeyboardInterrupt:
        agent_adapter.stop()
        logging.info("Edge stopped")
