import json
import logging
from typing import List

import pydantic_core
import requests

from app.entities.processed_agent_data import ProcessedAgentData
from app.interfaces.store_gateway import StoreGateway


class StoreApiAdapter(StoreGateway):
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url

    def save_data(self, processed_agent_data_batch: List[ProcessedAgentData]):
        """
        Save the processed road data to the Store API.
        Parameters:
            processed_agent_data_batch (List[ProcessedAgentData]): Processed road data to be saved.
        Returns:
            bool: True if the data is successfully saved, False otherwise.
        """
        try:
            # We need to send physical data structure that Store API expects
            # Store API expects List[ProcessedAgentData]
            payload = [item.model_dump() for item in processed_agent_data_batch]
            # Convert datetime to ISO string for JSON serialization
            for item in payload:
                item["agent_data"]["timestamp"] = item["agent_data"]["timestamp"].isoformat()
            
            response = requests.post(f"{self.api_base_url}/processed_agent_data/", json=payload)
            if response.status_code == 200 or response.status_code == 201:
                logging.info(f"Successfully saved {len(processed_agent_data_batch)} items to Store API")
                return True
            else:
                logging.error(f"Failed to save data. Status code: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            logging.error(f"Error connecting to Store API: {e}")
            return False

    def save_parking_data(self, data_batch: List[dict]):
        url = f"{self.api_base_url}/parking/"
        try:
            response = requests.post(url, json=data_batch)
            if response.status_code != 200:
                logging.error(f"Store API Error (Parking): {response.text}")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Failed to connect to Store API (Parking): {e}")
            return False

    def save_traffic_light_data(self, data_batch: List[dict]):
        url = f"{self.api_base_url}/traffic_light/"
        try:
            response = requests.post(url, json=data_batch)
            if response.status_code != 200:
                logging.error(f"Store API Error (Traffic Light): {response.text}")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Failed to connect to Store API (Traffic Light): {e}")
            return False