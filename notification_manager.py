# notification_manager.py
import os
from dotenv import load_dotenv
from twilio.rest import Client
from flight_data import FlightData
import requests

load_dotenv()

TWILIO_SID = os.environ["TWILIO_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_VIRTUAL_NUMBER = os.environ["TWILIO_VIRTUAL_NUMBER"]
TWILIO_VERIFIED_NUMBER = os.environ["TWILIO_VERIFIED_NUMBER"]
PUSHOVER_API_KEY = os.environ.get("PUSHOVER_API_KEY")
PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY")


class NotificationManager:
    """Responsible for sending notifications with the deal flight details via Pushover."""

    def __init__(self):
        self.api_url = "https://api.pushover.net/1/messages.json"
        self.user_key = PUSHOVER_API_KEY
        self.user_token = PUSHOVER_USER_KEY

    def send_notification(self, flight: FlightData, origin_code: str):
        message = (
            f"💸 Flight Deal Found!\n\n"
            f"{flight.origin_city} → {flight.destination_city}\n\n"
            f"Price: ${flight.price}\n"
            f"Flights: {flight.num_flights} total\n\n"
            f"Depart: {flight.out_date}\n"
            f"Return: {flight.return_date}"
        )

        pushover_data = {
            "token": self.user_key,
            "user": self.user_token,
            "message": message,
        }

        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data=pushover_data,
        )

        response.raise_for_status()
        print("📲 Pushover notification sent.")
