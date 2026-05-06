import json
import os
from csv import DictReader
from typing import List, Tuple


class FileDatasource:
    """
    Симулює рух машини: координати беруться з реального маршруту,
    стан дороги — з accelerometer CSV.
    """

    def __init__(self, csv_file: str, route_file: str | None = None):
        self.csv_file = csv_file
        self.route_file = route_file or os.path.join(
            os.path.dirname(csv_file), "route.json"
        )
        self.index = 0
        self._route: List[Tuple[float, float]] = self._load_route()
        self._data: List[Tuple[float, float, str]] = self._build_path()

    def _load_route(self) -> List[Tuple[float, float]]:
        """
        Завантажує waypoints з route.json (GeoJSON LineString).
        Повертає список (lat, lon).
        """
        if not os.path.exists(self.route_file):
            print(f"DEBUG: route.json not found at {self.route_file}, fallback to single point")
            return [(50.4501, 30.5234)]

        with open(self.route_file, encoding="utf-8") as f:
            geo = json.load(f)

        if isinstance(geo, dict) and geo.get("type") == "LineString":
            coords = geo["coordinates"]
            return [(lat, lon) for lon, lat in coords]
        elif isinstance(geo, list):
            return [(lat, lon) for lat, lon in geo]
        else:
            print(f"DEBUG: unsupported route format")
            return [(50.4501, 30.5234)]

    def _build_path(self) -> List[Tuple[float, float, float]]:
        """
        Читає accelerometer CSV.
        Для кожного запису обчислює:
         - позицію вздовж маршруту через лінійну інтерполяцію
         - сире значення z
        """
        try:
            with open(self.csv_file, mode="r", newline="", encoding="utf-8") as f:
                rows = list(DictReader(f))
        except Exception as e:
            print(f"DEBUG: FileDatasource failed to load: {e}")
            return []

        n_rows = len(rows)
        n_route = len(self._route)

        if n_rows == 0 or n_route < 2:
            return []

        result = []

        for i, row in enumerate(rows):
            try:
                z = float(row.get("Z", 0))
            except (ValueError, TypeError):
                continue

            progress = i / (n_rows - 1) if n_rows > 1 else 0.0
            seg_float = progress * (n_route - 1)
            seg_idx = min(int(seg_float), n_route - 2)
            t = seg_float - seg_idx

            lat1, lon1 = self._route[seg_idx]
            lat2, lon2 = self._route[seg_idx + 1]

            lat = lat1 + (lat2 - lat1) * t
            lon = lon1 + (lon2 - lon1) * t

            result.append((lat, lon, z))

        print(
            f"DEBUG: FileDatasource built {len(result)} points "
            f"along {n_route}-waypoint route"
        )

        return result

    def get_new_points(self, batch_size: int = 1) -> List[Tuple[float, float, float]]:
        """Циклічне читання — машина їздить безкінечно по маршруту."""
        if not self._data:
            return []
    
        result = []
    
        for _ in range(batch_size):
            result.append(self._data[self.index])
            self.index = (self.index + 1) % len(self._data)
    
        return result