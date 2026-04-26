from dataclasses import dataclass
from datetime import datetime
from domain.gps import Gps

@dataclass
class TrafficLight:
    user_id: int
    light_id: str
    current_state: str
    car_count: int
    gps: Gps
    timestamp: datetime
