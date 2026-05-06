from csv import DictReader
from datetime import datetime
from typing import List, Optional

import config
from shared.sensor import (
    SensorReading,
    GpsData,
    AccelerometerData,
    RoadPayload,
    ParkingPayload,
    TrafficLightPayload,
    NetworkPayload,
)


def _parse_bool(s) -> bool:
    return str(s).strip().lower() in ("1", "true", "yes", "y", "t")


class FileDatasource:
    """
    Читає sensor-дані з CSV файлів і повертає їх як SensorReading об'єкти.
    Один інстанс може обслуговувати декілька джерел (road, parking, traffic_light).
    """

    def __init__(
        self,
        accelerometer_filename: Optional[str] = None,
        gps_filename: Optional[str] = None,
        parking_filename: Optional[str] = None,
        traffic_light_filename: Optional[str] = None,
        network_filename: Optional[str] = None,
    ):
        self.filenames = {
            "accel": accelerometer_filename,
            "gps": gps_filename,
            "parking": parking_filename,
            "traffic_light": traffic_light_filename,
            "network": network_filename,
        }
        self.files = {}
        self.readers = {}

    def read(self) -> List[SensorReading]:
        """Road readings: спарені accelerometer + GPS на кожен tick."""
        batch = []
        for _ in range(config.BATCH_SIZE):
            acc_row = self._get_next_row("accel")
            gps_row = self._get_next_row("gps")
            batch.append(SensorReading(
                sensor_id=f"car_{config.USER_ID}",
                user_id=config.USER_ID,
                gps=GpsData(
                    latitude=float(gps_row["latitude"]),
                    longitude=float(gps_row["longitude"]),
                ),
                timestamp=datetime.now(),
                payload=RoadPayload(
                    accelerometer=AccelerometerData(
                        x=float(acc_row["x"]),
                        y=float(acc_row["y"]),
                        z=float(acc_row["z"]),
                    ),
                    road_state=None,  # заповнить Edge після класифікації
                ),
            ))
        return batch

    def read_parking(self) -> List[SensorReading]:
        batch = []
        for _ in range(config.BATCH_SIZE):
            row = self._get_next_row("parking")
            batch.append(SensorReading(
                sensor_id=row["parking_id"],
                user_id=config.USER_ID,
                gps=GpsData(
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                ),
                timestamp=datetime.now(),
                payload=ParkingPayload(
                    is_occupied=_parse_bool(row["is_occupied"]),
                    total_spots=int(row["total_spots"]),
                ),
            ))
        return batch

    def read_traffic_light(self) -> List[SensorReading]:
        batch = []
        for _ in range(config.BATCH_SIZE):
            row = self._get_next_row("traffic_light")
            batch.append(SensorReading(
                sensor_id=row["light_id"],
                user_id=config.USER_ID,
                gps=GpsData(
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                ),
                timestamp=datetime.now(),
                payload=TrafficLightPayload(
                    current_state=row["current_state"],
                    car_count=int(row["car_count"]),
                ),
            ))
        return batch

    def read_network(self) -> List[SensorReading]:
        batch = []
        for _ in range(config.BATCH_SIZE):
            row = self._get_next_row("network")
            batch.append(SensorReading(
                sensor_id=row["node_id"],
                user_id=config.USER_ID,
                gps=GpsData(
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                ),
                timestamp=datetime.now(),
                payload=NetworkPayload(
                    latency_ms=float(row["latency_ms"]),
                    packet_loss_pct=float(row["packet_loss_pct"]),
                    throughput_kbps=float(row["throughput_kbps"]),
                    rssi_dbm=float(row["rssi_dbm"]),
                ),
            ))
        return batch

    def startReading(self, *args, **kwargs):
        for key, fname in self.filenames.items():
            if fname:
                f = open(fname, "r")
                self.files[key] = f
                self.readers[key] = DictReader(f)

    def stopReading(self, *args, **kwargs):
        for f in self.files.values():
            if f:
                f.close()
        self.files = {}
        self.readers = {}

    def _get_next_row(self, key: str):
        """Auto-rewind при досягненні EOF — циклічне читання."""
        try:
            return next(self.readers[key])
        except (StopIteration, TypeError, KeyError):
            self.files[key].seek(0)
            self.readers[key] = DictReader(self.files[key])
            return next(self.readers[key])
