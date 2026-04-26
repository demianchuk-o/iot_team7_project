from csv import DictReader
from datetime import datetime
from typing import List, Optional
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.aggregated_data import AggregatedData
from domain.parking import Parking
from domain.traffic_light import TrafficLight
import config

class FileDatasource:
    def __init__(
        self,
            accelerometer_filename: Optional[str] = None,
            gps_filename: Optional[str] = None,
        parking_filename: Optional[str] = None,
        traffic_light_filename: Optional[str] = None,
    ) -> None:
        self.filenames = {
            'accel': accelerometer_filename,
            'gps': gps_filename,
            'parking': parking_filename,
            'traffic_light': traffic_light_filename
        }
        self.files = {}
        self.readers = {}

    def read(self) -> List[AggregatedData]:
        """Метод повертає дані отримані з датчиків батчами"""
        data_batch: List[AggregatedData] = []
        batch_size = config.BATCH_SIZE
        for _ in range(batch_size):
            acc_row = self._get_next_row('accel')
            gps_row = self._get_next_row('gps')
            data_batch.append(AggregatedData(
                Accelerometer(int(acc_row['x']), int(acc_row['y']), int(acc_row['z'])),
                Gps(float(gps_row['longitude']), float(gps_row['latitude'])),
                datetime.now(),
                config.USER_ID,
            ))
            
        return data_batch

    def read_parking(self) -> List[dict]:
        """Метод для читання даних про парковку"""
        data_batch = []
        batch_size = config.BATCH_SIZE
        for _ in range(batch_size):
            row = self._get_next_row('parking')
            data_batch.append(Parking(
                config.USER_ID,
                row['parking_id'],
                bool(int(row['is_occupied'])),
                int(row['total_spots']),
                Gps(longitude=float(row['longitude']), latitude=float(row['latitude'])),
                datetime.now(),
            ))
        return data_batch

    def read_traffic_light(self) -> List[dict]:
        """Метод для читання даних про світлофори"""
        data_batch = []
        batch_size = config.BATCH_SIZE
        for _ in range(batch_size):
            row = self._get_next_row('traffic_light')
            data_batch.append(TrafficLight(
                config.USER_ID,
                row['light_id'],
                row['current_state'],
                int(row['car_count']),
                Gps(longitude=float(row['longitude']), latitude=float(row['latitude'])),
                datetime.now(),
            ))
        return data_batch

    def startReading(self, *args, **kwargs):
        """Метод повинен викликатись перед початком читання даних"""
        for key, filename in self.filenames.items():
            if filename:
                f = open(filename, 'r')
                self.files[key] = f
                self.readers[key] = DictReader(f)

    def stopReading(self, *args, **kwargs):
        """Метод повинен викликатись для закінчення читання даних"""
        for f in self.files.values():
            if f:
                f.close()
        self.files = {}
        self.readers = {}

    def _get_next_row(self, reader_key):
        """Допоміжний метод для отримання наступного рядка з автоматичним скиданням файлу"""
        try:
            return next(self.readers[reader_key])
        except (StopIteration, TypeError, KeyError):
            self.files[reader_key].seek(0)
            self.readers[reader_key] = DictReader(self.files[reader_key])
            return next(self.readers[reader_key])