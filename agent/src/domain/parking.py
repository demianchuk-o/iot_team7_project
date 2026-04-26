from dataclasses import dataclass
from datetime import datetime
from domain.gps import Gps

@dataclass
class Parking:
    user_id: int
    parking_id: str
    is_occupied: bool
    total_spots: int
    gps: Gps
    timestamp: datetime
