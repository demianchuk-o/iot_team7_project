from shared.sensor import SensorReading, RoadPayload, NetworkPayload
from shared.road_classifier import classify_road


def _classify_network(payload: NetworkPayload) -> tuple[float, str]:
    """Rule-based anomaly score for simple real-time network monitoring."""
    score = 0.0

    if payload.latency_ms > 120:
        score += 0.35
    elif payload.latency_ms > 80:
        score += 0.2

    if payload.packet_loss_pct > 5:
        score += 0.35
    elif payload.packet_loss_pct > 2:
        score += 0.2

    if payload.throughput_kbps < 450:
        score += 0.2
    elif payload.throughput_kbps < 700:
        score += 0.1

    if payload.rssi_dbm < -80:
        score += 0.2
    elif payload.rssi_dbm < -70:
        score += 0.1

    score = min(round(score, 2), 1.0)
    if score >= 0.65:
        return score, "critical"
    if score >= 0.35:
        return score, "warning"
    return score, "normal"


def process_sensor_reading(reading: SensorReading) -> SensorReading:
    if isinstance(reading.payload, RoadPayload):
        z = reading.payload.accelerometer.z

        new_payload = reading.payload.model_copy(
            update={"road_state": classify_road(z)}
        )

        return reading.model_copy(update={"payload": new_payload})

    if isinstance(reading.payload, NetworkPayload):
        anomaly_score, network_state = _classify_network(reading.payload)
        new_payload = reading.payload.model_copy(
            update={
                "anomaly_score": anomaly_score,
                "network_state": network_state,
            }
        )
        return reading.model_copy(update={"payload": new_payload})

    return reading
