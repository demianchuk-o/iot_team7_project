import logging
import threading
import time

from paho.mqtt import client as mqtt_client

import config
from file_datasource import FileDatasource

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [agent] %(message)s",
)
log = logging.getLogger(__name__)


def connect_mqtt(broker: str, port: int) -> mqtt_client.Client:
    log.info(f"Connecting to MQTT {broker}:{port}")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            log.info(f"Connected to MQTT Broker ({broker}:{port})")
        else:
            log.error(f"MQTT connection failed: rc={rc}")

    client = mqtt_client.Client()
    client.on_connect = on_connect
    client.connect(broker, port)
    client.loop_start()
    return client


def publish_loop(client, topic: str, datasource: FileDatasource, delay: float, read_method):
    """Періодично читає батч SensorReading-ів і публікує в MQTT-топік."""
    datasource.startReading()
    try:
        while True:
            time.sleep(delay)
            try:
                batch = read_method()
            except Exception as e:
                log.error(f"[{topic}] read error: {e}")
                continue
            for reading in batch:
                msg = reading.model_dump_json()
                result = client.publish(topic, msg)
                if result[0] == 0:
                    log.info(f"[{topic}] sent {reading.payload.sensor_type}/{reading.sensor_id}")
                else:
                    log.error(f"[{topic}] publish FAILED status={result[0]}")
    except Exception as e:
        log.error(f"[{topic}] fatal: {e}")
    finally:
        datasource.stopReading()


def run():
    client = connect_mqtt(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)

    # Кожен сенсор живе в окремому потоці і шле в свій топік.
    # Конвенція: sensors/<type>/raw — необроблені дані від датчика.
    threads = []

    # Road
    road_ds = FileDatasource(
        accelerometer_filename="data/accelerometer.csv",
        gps_filename="data/gps.csv",
    )
    threads.append(threading.Thread(
        target=publish_loop,
        args=(client, "sensors/road/raw", road_ds, config.DELAY, road_ds.read),
        daemon=True,
        name="road",
    ))

    # Parking
    parking_ds = FileDatasource(parking_filename="data/parking.csv")
    threads.append(threading.Thread(
        target=publish_loop,
        args=(client, "sensors/parking/raw", parking_ds, 2.0, parking_ds.read_parking),
        daemon=True,
        name="parking",
    ))

    # Traffic light
    tl_ds = FileDatasource(traffic_light_filename="data/traffic_lights.csv")
    threads.append(threading.Thread(
        target=publish_loop,
        args=(client, "sensors/traffic_light/raw", tl_ds, 1.0, tl_ds.read_traffic_light),
        daemon=True,
        name="traffic_light",
    ))

    # Network telemetry
    network_ds = FileDatasource(network_filename="data/network.csv")
    threads.append(threading.Thread(
        target=publish_loop,
        args=(client, "sensors/network/raw", network_ds, 1.5, network_ds.read_network),
        daemon=True,
        name="network",
    ))

    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    run()
