"""
ISS Location Tracker
Fetches the current ISS position and reverse geocodes it via Google Maps API.
"""

import os
import math
import sqlite3
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

ISS_API_URL        = "https://api.wheretheiss.at/v1/satellites/25544"
GEOCODE_API_URL    = "https://maps.googleapis.com/maps/api/geocode/json"
DB_PATH            = "iss_locations.db"

# ── Fetch ISS position ───────────────────────────────────────────────────────
def get_iss_position() -> dict:
    """Return current ISS latitude, longitude, and timestamp."""
    response = requests.get(ISS_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()

    return {
        "latitude":  float(data["latitude"]),
        "longitude": float(data["longitude"]),
        "timestamp": datetime.fromtimestamp(data["timestamp"], tz=timezone.utc),
    }

# ── Reverse geocode ──────────────────────────────────────────────────────────
def reverse_geocode(lat: float, lng: float, api_key: str) -> dict:
    """
    Use Google Maps Geocoding API to resolve lat/lng to a human-readable location.
    Returns a dict with 'city', 'country', and 'formatted_address'.
    """
    params = {
        "latlng": f"{lat},{lng}",
        "key":    api_key,
    }
    response = requests.get(GEOCODE_API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    status = data.get("status")
    if status == "ZERO_RESULTS":
        return {
            "city":              "Over ocean / unpopulated area",
            "country":           "N/A",
            "formatted_address": f"{lat:.4f}, {lng:.4f}",
        }

    if status != "OK":
        raise RuntimeError(f"Geocoding API error: {status} — {data.get('error_message', '')}")

    # Parse the most detailed result
    result     = data["results"][0]
    components = result.get("address_components", [])

    city    = next(
        (c["long_name"] for c in components if "locality" in c["types"]), None
    ) or next(
        (c["long_name"] for c in components if "administrative_area_level_1" in c["types"]), None
    )
    country = next(
        (c["long_name"] for c in components if "country" in c["types"]), None
    )

    # Only a Plus Code returned → open ocean or unpopulated region
    if not city and not country:
        return {
            "city":              "Over ocean / unpopulated area",
            "country":           "N/A",
            "formatted_address": result.get("formatted_address", f"{lat:.4f}, {lng:.4f}"),
        }

    return {
        "city":              city or "Unknown",
        "country":           country or "Unknown",
        "formatted_address": result.get("formatted_address", ""),
    }

# ── Haversine distance ───────────────────────────────────────────────────────
def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return the great-circle distance in km between two lat/lng points."""
    R = 6371  # Earth's radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(d_lng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

# ── SQLite ───────────────────────────────────────────────────────────────────
def init_db() -> None:
    """Create the iss_locations table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS iss_locations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                latitude    REAL    NOT NULL,
                longitude   REAL    NOT NULL,
                city        TEXT,
                country     TEXT,
                distance_km REAL
            )
        """)

def save_to_db(timestamp: str, lat: float, lng: float,
               city: str, country: str, distance_km: float) -> None:
    """Insert one ISS location record into the database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO iss_locations (timestamp, latitude, longitude, city, country, distance_km)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, lat, lng, city, country, distance_km))

# ── SMS alert via Textbelt ───────────────────────────────────────────────────
TEXTBELT_URL = "https://textbelt.com/text"

def send_sms(recipients: list[str], message: str) -> None:
    """Send an SMS to each recipient using the free Textbelt API."""
    for number in recipients:
        resp = requests.post(TEXTBELT_URL, data={
            "phone":   number.strip(),
            "message": message,
            "key":     "textbelt",
        }, timeout=10)
        result = resp.json()
        status = "sent" if result.get("success") else f"failed ({result.get('error', 'unknown')})"
        print(f"  SMS to {number}: {status}")

# ── Main ─────────────────────────────────────────────────────────────────────
MY_LAT = 13.995834
MY_LNG = 120.826451

def main():
    recipients         = [n for n in os.environ.get("SMS_RECIPIENTS", "").split(",") if n.strip()]
    proximity_threshold = float(os.environ.get("PROXIMITY_THRESHOLD_KM", 6))

    if not GOOGLE_MAPS_API_KEY:
        raise EnvironmentError(
            "GOOGLE_MAPS_API_KEY is not set.\n"
            "Export it before running:\n"
            "  export GOOGLE_MAPS_API_KEY='your_key_here'"
        )

    init_db()

    print("Fetching ISS position …")
    pos = get_iss_position()

    lat, lng = pos["latitude"], pos["longitude"]
    ts       = pos["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC")

    print(f"\nTimestamp : {ts}")
    print(f"Latitude  : {lat}")
    print(f"Longitude : {lng}")

    print("\nReverse geocoding via Google Maps …")
    location = reverse_geocode(lat, lng, GOOGLE_MAPS_API_KEY)

    print(f"\nCity      : {location['city']}")
    print(f"Country   : {location['country']}")
    print(f"Address   : {location['formatted_address']}")
    print(f"\nGoogle Maps link: https://www.google.com/maps?q={lat},{lng}")

    my_location = reverse_geocode(MY_LAT, MY_LNG, GOOGLE_MAPS_API_KEY)
    distance = haversine_km(MY_LAT, MY_LNG, lat, lng)
    print(f"\n── Distance from your location ──────────────────")
    print(f"Your city     : {my_location['city']}, {my_location['country']}")
    print(f"Your location : {MY_LAT}, {MY_LNG}")
    print(f"ISS location  : {lat}, {lng}")
    print(f"Distance      : {distance:,.2f} km")

    # ── Save to SQLite ────────────────────────────────────────────────────────
    save_to_db(ts, lat, lng, location["city"], location["country"], distance)
    print(f"\nRecord saved to {DB_PATH}")

    # ── Proximity SMS alert ───────────────────────────────────────────────────
    if distance <= proximity_threshold:
        print(f"\n*** ISS is within {proximity_threshold} km! Sending SMS alert …")
        message = (
            f"ISS ALERT: The ISS is only {distance:.2f} km from your location!\n"
            f"Your city : {my_location['city']}, {my_location['country']}\n"
            f"ISS pos   : {lat:.4f}, {lng:.4f}\n"
            f"Maps      : https://www.google.com/maps?q={lat},{lng}"
        )
        send_sms(recipients, message)
    else:
        print(f"\nNo alert — ISS is {distance:,.2f} km away (threshold: {proximity_threshold} km)")


if __name__ == "__main__":
    main()
