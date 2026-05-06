from abc import ABC, abstractmethod

from shared.sensor import SensorReading


class HubGateway(ABC):
    @abstractmethod
    def save_data(self, reading: SensorReading, topic: str) -> bool:
        """Відправляє оброблений reading у вказаний топік. Повертає True у випадку успіху."""
        pass
