from abc import ABC, abstractmethod
from typing import List

from shared.sensor import SensorReading


class StoreGateway(ABC):
    """Абстракція доступу до Store API."""

    @abstractmethod
    def save_sensor_batch(self, batch: List[SensorReading]) -> bool:
        """Зберегти батч показань. Повертає True у випадку успіху."""
        pass
