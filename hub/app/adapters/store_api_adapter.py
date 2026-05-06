import logging
from typing import List

import requests

from app.interfaces.store_gateway import StoreGateway
from shared.sensor import SensorReading


class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    def save_sensor_batch(self, batch: List[SensorReading]) -> bool:
        """Універсальна відправка батчу будь-якого типу сенсорів у Store API."""
        if not batch:
            return True
        try:
            payload = []
            for r in batch:
                d = r.model_dump()
                d["timestamp"] = d["timestamp"].isoformat()
                payload.append(d)

            response = requests.post(
                f"{self.api_base_url}/sensors/",
                json=payload,
                timeout=10,
            )
            if response.status_code in (200, 201):
                logging.info(f"Saved {len(batch)} sensor readings to Store")
                return True
            logging.error(
                f"Store API error: {response.status_code} - {response.text[:200]}"
            )
            return False
        except Exception as e:
            logging.error(f"Failed to save sensor batch: {e}")
            return False
