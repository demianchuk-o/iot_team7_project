from csv import DictReader
from datetime import datetime
from typing import List
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.aggregated_data import AggregatedData
import config


class FileDatasource:
    def __init__(
        self,
        accelerometer_filename: str,
        gps_filename: str,
    ) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        self.accelerometer_file = None
        self.gps_file = None
        self.accelerometer_reader = None
        self.gps_reader = None

    def read(self) -> List[AggregatedData]:
        """Метод повертає дані отримані з датчиків батчами"""
        data_batch: List[AggregatedData] = []
        
        batch_size = config.BATCH_SIZE
        
        for _ in range(batch_size):
            try:
                acc_row = next(self.accelerometer_reader)
                gps_row = next(self.gps_reader)
            except (StopIteration, TypeError):
                # Reset readers if end of file or not started
                self.stopReading()
                self.startReading()
                acc_row = next(self.accelerometer_reader)
                gps_row = next(self.gps_reader)

            data_batch.append(AggregatedData(
                Accelerometer(int(acc_row['x']), int(acc_row['y']), int(acc_row['z'])),
                Gps(float(gps_row['longitude']), float(gps_row['latitude'])),
                datetime.now(),
                config.USER_ID,
            ))
            
        return data_batch

    def startReading(self, *args, **kwargs):
        """Метод повинен викликатись перед початком читання даних"""
        self.accelerometer_file = open(self.accelerometer_filename, 'r')
        self.gps_file = open(self.gps_filename, 'r')
        self.accelerometer_reader = DictReader(self.accelerometer_file)
        self.gps_reader = DictReader(self.gps_file)

    def stopReading(self, *args, **kwargs):
        """Метод повинен викликатись для закінчення читання даних"""
        if self.accelerometer_file:
            self.accelerometer_file.close()
            self.accelerometer_file = None
        if self.gps_file:
            self.gps_file.close()
            self.gps_file = None
