from paho.mqtt import client as mqtt_client
import threading
import time
from schema.aggregated_data_schema import AggregatedDataSchema
from schema.parking_schema import ParkingSchema
from schema.traffic_light_schema import TrafficLightSchema
from file_datasource import FileDatasource
import config

road_schema = AggregatedDataSchema()
parking_schema = ParkingSchema()
traffic_light_schema = TrafficLightSchema()

def connect_mqtt(broker, port):
    """Create MQTT client"""
    print(f"CONNECT TO {broker}:{port}")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT Broker ({broker}:{port})!", flush=True)
        else:
            print(f"Failed to connect {broker}:{port}, return code %d\n", rc, flush=True)
            exit(rc)  # Stop execution

    client = mqtt_client.Client()
    client.on_connect = on_connect
    client.connect(broker, port)
    client.loop_start()
    return client


def publish(client, topic, datasource, delay, schema, read_method):
    datasource.startReading()
    try:
        while True:
            time.sleep(delay)
            # read_method: read, read_parking or read_traffic_light
            data_batch = read_method()
            for data in data_batch:
                msg = schema.dumps(data)
                result = client.publish(topic, msg)
                if result[0] == 0:
                    print(f"[{topic}] Sent message", flush=True)
                else:
                    print(f"[{topic}] Failed to send", flush=True)
    except Exception as e:
        print(f"Error in {topic}: {e}")
    finally:
        datasource.stopReading()


def run():
    # Prepare mqtt client
    client = connect_mqtt(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)
    # Prepare datasource
    # Roads
    road_ds = FileDatasource(accelerometer_filename="data/accelerometer.csv", gps_filename="data/gps.csv")
    road_thread = threading.Thread(target=publish, args=(
        client, config.MQTT_TOPIC, road_ds, config.DELAY, road_schema, road_ds.read
    ))
    # Parkings
    parking_ds = FileDatasource(parking_filename="data/parking.csv")
    parking_thread = threading.Thread(target=publish, args=(
        client, "agent/parking/data", parking_ds, 2.0, parking_schema, parking_ds.read_parking
    ))
    # Traffic Lights
    traffic_ds = FileDatasource(traffic_light_filename="data/traffic_lights.csv")
    traffic_thread = threading.Thread(target=publish, args=(
        client, "agent/traffic_light/data", traffic_ds, 1.0, traffic_light_schema, traffic_ds.read_traffic_light
    ))

    road_thread.start()
    parking_thread.start()
    traffic_thread.start()

    road_thread.join()
    parking_thread.join()
    traffic_thread.join()


if __name__ == "__main__":
    run()
