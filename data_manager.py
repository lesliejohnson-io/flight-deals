# data_manager.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SHEETY_ENDPOINT = os.environ["SHEETY_ENDPOINT"]
SHEETY_TOKEN = os.environ["SHEETY_TOKEN"]


class DataManager:
    """Responsible for talking to the Google Sheet via Sheety."""

    def __init__(self):
        self.sheety_endpoint = SHEETY_ENDPOINT
        self.headers = {
            "Authorization": f"Bearer {SHEETY_TOKEN}",
            "Content-Type": "application/json",
        }
        self.destination_data = []

    def get_destination_data(self):
        response = requests.get(self.sheety_endpoint, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        self.destination_data = data["prices"]
        return self.destination_data

    def update_destination_codes(self):
        """Update iataCode, lowestPrice, and numFlights back to the sheet."""
        for row in self.destination_data:
            row_id = row["id"]

            payload = {
                "price": {
                    "city":        row["city"],
                    "iataCode":    row["iataCode"],
                    # default 0 if missing, to avoid KeyError
                    "lowestPrice": row.get("lowestPrice", 0),
                    "numFlights":  row.get("numFlights", 0),
                }
            }

            put_url = f"{self.sheety_endpoint}/{row_id}"
            response = requests.put(
                put_url,
                headers=self.headers,
                json=payload,
            )
            print(f"Updating row {row_id}: {response.status_code}")
            print(response.text)
            response.raise_for_status()
