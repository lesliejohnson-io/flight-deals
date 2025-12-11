# main.py
from datetime import datetime, timedelta
from data_manager import DataManager
from flight_search import FlightSearch
from notification_manager import NotificationManager

# Change this to origin airport code:
ORIGIN_AIRPORT = "ORD"
ORIGIN_CITY_NAME = "Chicago"

data_manager = DataManager()
flight_search = FlightSearch()
notification_manager = NotificationManager()

# 1. Get destination data from Google Sheet
sheet_data = data_manager.get_destination_data()

# 2. Compute date window: tomorrow to ~6 months from now
tomorrow = datetime.now() + timedelta(days=1)
six_months = datetime.now() + timedelta(days=6 * 30)

departure_date = tomorrow.strftime("%Y-%m-%d")
return_date = six_months.strftime("%Y-%m-%d")

# 3. Loop through each destination
for row in sheet_data:
    dest_city = row["city"]
    dest_code = row["iataCode"]
    lowest_price_threshold = float(row.get("lowestPrice", 999999))

    flight = flight_search.search_cheapest_flight(
        origin_code=ORIGIN_AIRPORT,
        destination_code=dest_code,
        departure_date=departure_date,
        return_date=return_date,
        destination_city=dest_city,         # from sheet
        origin_city=ORIGIN_CITY_NAME,       # from main.py
    )

    row["numFlights"] = flight.num_flights
    print(f"{ORIGIN_AIRPORT} → {dest_city}: {flight.price} ({flight.num_flights} flights)")

    if flight.price != "N/A":
        try:
            current_price = float(flight.price)
        except ValueError:
            current_price = 999999

        if current_price < lowest_price_threshold:
            notification_manager.send_notification(flight, origin_code=ORIGIN_AIRPORT)


# 5. Push updated numFlights (and any edited lowestPrice) back to the sheet
data_manager.destination_data = sheet_data
data_manager.update_destination_codes()
