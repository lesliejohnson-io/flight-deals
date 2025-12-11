# flight_search.py
import os
import time
import requests
from dotenv import load_dotenv
from flight_data import FlightData

load_dotenv()

AMADEUS_API_KEY = os.environ["AMADEUS_API_KEY"]
AMADEUS_API_SECRET = os.environ["AMADEUS_API_SECRET"]


class FlightSearch:
    def __init__(self):
        self.auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        self.city_search_url = "https://test.api.amadeus.com/v1/reference-data/locations"
        self.flight_offers_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        self.access_token = self._get_access_token()

    def _get_access_token(self):
        data = {
            "grant_type": "client_credentials",
            "client_id": AMADEUS_API_KEY,
            "client_secret": AMADEUS_API_SECRET,
        }
        response = requests.post(self.auth_url, data=data)
        response.raise_for_status()
        return response.json()["access_token"]

    def get_iata_code(self, city_name: str) -> str:
        """Look up a CITY-level IATA code from a city name."""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {
            "keyword": city_name,
            "subType": "CITY",
        }

        for attempt in range(5):
            response = requests.get(self.city_search_url, headers=headers, params=params)

            if response.status_code == 429:
                wait = 2 ** attempt
                print(f"Rate limit (IATA) for {city_name}. Waiting {wait}s...")
                time.sleep(wait)
                continue

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                return ""

            data = response.json()
            try:
                return data["data"][0]["iataCode"]
            except (KeyError, IndexError):
                return ""

        return ""

    def search_cheapest_flight(
        self,
        origin_code: str,
        destination_code: str,
        departure_date: str,
        return_date: str,
        destination_city: str,
        origin_city: str | None = None,
    ) -> FlightData:
        """
        Search for the cheapest round-trip flight between origin_code and destination_code.
        destination_city comes from the Google Sheet.
        origin_city can be passed from main.py (e.g. 'Chicago') or fall back to origin_code.
        """

        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {
            "originLocationCode": origin_code,
            "destinationLocationCode": destination_code,
            "departureDate": departure_date,
            "returnDate": return_date,
            "adults": 1,
            "currencyCode": "USD",
            # allow connections: no nonStop filter
            "max": 30,
        }

        for attempt in range(5):
            response = requests.get(self.flight_offers_url, headers=headers, params=params)

            if response.status_code == 429:
                wait = 2 ** attempt
                print(f"Rate limit (offers) for {origin_code}->{destination_code}. Waiting {wait}s...")
                time.sleep(wait)
                continue

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                # If the call fails, return an N/A FlightData using the nicest names we have.
                return FlightData(
                    price="N/A",
                    origin_city=origin_city or origin_code,
                    origin_airport="N/A",
                    destination_city=destination_city or destination_code,
                    destination_airport="N/A",
                    out_date="N/A",
                    return_date="N/A",
                    num_flights=0,
                )

            data = response.json()
            offers = data.get("data", [])

            if not offers:
                print(f"No offers found for {origin_code}->{destination_code}")
                return FlightData(
                    price="N/A",
                    origin_city=origin_city or origin_code,
                    origin_airport="N/A",
                    destination_city=destination_city or destination_code,
                    destination_airport="N/A",
                    out_date="N/A",
                    return_date="N/A",
                    num_flights=0,
                )

            # Cheapest by price
            cheapest = min(offers, key=lambda o: float(o["price"]["total"]))
            price = cheapest["price"]["total"]

            itineraries = cheapest["itineraries"]

            # Total segments (flights) across all itineraries (outbound + return)
            total_segments = sum(len(it["segments"]) for it in itineraries)

            # Outbound leg
            out_itinerary = itineraries[0]
            out_segments = out_itinerary["segments"]
            origin_airport = out_segments[0]["departure"]["iataCode"]
            destination_airport = out_segments[-1]["arrival"]["iataCode"]
            out_date = out_segments[0]["departure"]["at"].split("T")[0]

            # Return leg (if present)
            if len(itineraries) > 1:
                return_itinerary = itineraries[1]
                return_segments = return_itinerary["segments"]
                return_date_str = return_segments[0]["departure"]["at"].split("T")[0]
            else:
                return_date_str = "N/A"

            # --- Use Amadeus dictionaries for COUNTRY codes only ---
            locations = data.get("dictionaries", {}).get("locations", {})

            origin_loc = locations.get(origin_airport, {})
            dest_loc = locations.get(destination_airport, {})

            origin_country_code = origin_loc.get("countryCode", "").upper()
            dest_country_code = dest_loc.get("countryCode", "").upper()

            # Prefer sheet/origin names over API city codes
            origin_city_name = origin_city or origin_code
            dest_city_name = destination_city or destination_code

            if origin_country_code:
                origin_city_display = f"{origin_city_name}, {origin_country_code}"
            else:
                origin_city_display = origin_city_name

            if dest_country_code:
                destination_city_display = f"{dest_city_name}, {dest_country_code}"
            else:
                destination_city_display = dest_city_name

            return FlightData(
                price=price,
                origin_city=origin_city_display,
                origin_airport=origin_airport,
                destination_city=destination_city_display,
                destination_airport=destination_airport,
                out_date=out_date,
                return_date=return_date_str,
                num_flights=total_segments,
            )

        # All retries failed
        return FlightData(
            price="N/A",
            origin_city=origin_city or origin_code,
            origin_airport="N/A",
            destination_city=destination_city or destination_code,
            destination_airport="N/A",
            out_date="N/A",
            return_date="N/A",
            num_flights=0,
        )
