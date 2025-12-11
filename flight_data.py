# flight_data.py
from dataclasses import dataclass

@dataclass
class FlightData:
    price: str                  # keep as string because Amadeus gives "822.63"; we’ll cast when comparing
    origin_city: str
    origin_airport: str
    destination_city: str
    destination_airport: str
    out_date: str
    return_date: str
    num_flights: int            # total number of segments (outbound + inbound)
