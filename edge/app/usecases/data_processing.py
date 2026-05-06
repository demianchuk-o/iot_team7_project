from shared.sensor import SensorReading, RoadPayload
from shared.road_classifier import classify_road


def process_sensor_reading(reading: SensorReading) -> SensorReading:
    if not isinstance(reading.payload, RoadPayload):
        return reading

    z = reading.payload.accelerometer.z

    new_payload = reading.payload.model_copy(
        update={"road_state": classify_road(z)}
    )

    return reading.model_copy(update={"payload": new_payload})