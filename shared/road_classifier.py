from typing import Literal

RoadState = Literal["normal", "small pits", "large pits"]


def classify_road(z: float) -> RoadState:
    """Класифікація стану дороги за Z-axis accelerometer'а."""
    if 14000 <= z <= 18000:
        return "normal"

    if (12000 <= z < 14000) or (18000 < z <= 20000):
        return "small pits"

    return "large pits"