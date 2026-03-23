from csv import DictReader
from typing import List, Tuple

class FileDatasource:
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.index = 0
        self._data = self._load_data()

    def _load_data(self) -> List[Tuple[float, float, str]]:
        """
        Loads data from local data.csv using standard csv module.
        Calculates fake GPS coordinates using base offset logic.
        """
        processed_points = []
        try:
            with open(self.csv_file, mode='r', newline='') as f:
                reader = DictReader(f)
                # Base Kyiv coordinates for the fake GPS offset
                base_lat, base_lon = 50.4501, 30.5234
                
                for row in reader:
                    try:
                        x = float(row.get('X', 0))
                        y = float(row.get('Y', 0))
                        z = float(row.get('Z', 0))
                        
                        # Perform classification logic (same as Edge)
                        if 14000 <= z <= 18000:
                            state = "normal"
                        elif (12000 <= z < 14000) or (18000 < z <= 20000):
                            state = "small pits"
                        else:
                            state = "large pits"
                        
                        # Purely empirical offset logic for demonstration
                        lat = base_lat + (x / 1000000)
                        lon = base_lon + (y / 1000000)
                        
                        processed_points.append((lat, lon, state))
                    except (ValueError, TypeError):
                        continue
            
            print(f"DEBUG: FileDatasource loaded {len(processed_points)} points")
            return processed_points
        except Exception as e:
            print(f"DEBUG: FileDatasource failed to load: {e}")
            return []

    def get_new_points(self, batch_size: int = 1) -> List[Tuple[float, float, str]]:
        """Returns a small batch of points to prevent UI flooding"""
        if self.index >= len(self._data):
            return []
            
        end_idx = min(self.index + batch_size, len(self._data))
        points = self._data[self.index:end_idx]
        self.index = end_idx
        return points
