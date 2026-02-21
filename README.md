# ISS Location Tracker
<img width="2788" height="1448" alt="8E10B7DB-2A77-4D40-B7A6-C0A10AF8DD82" src="https://github.com/user-attachments/assets/f22d67ba-c23f-44dd-96e2-3759a23312f0" />



A Python tool that fetches the real-time position of the International Space Station (ISS), reverse geocodes it to a human-readable city/country via the Google Maps API, computes the distance from your location, sends an SMS alert when the ISS is nearby, saves every reading to SQLite, and visualizes the full history on an interactive Streamlit dashboard.

## Features

- Real-time ISS latitude & longitude via [Where the ISS at?](https://wheretheiss.at/) API
- Reverse geocoding using Google Maps Geocoding API
- Shows your own city from your coordinates
- Gracefully handles ocean/unpopulated areas
- Haversine distance calculation from your location to the ISS
- SMS alert via [Textbelt](https://textbelt.com) when ISS is within a configurable threshold (default 6 km)
- Saves every run to a local SQLite database
- Interactive Streamlit dashboard with a real map, animated ISS path, and distance chart

## Sample Output

```
Fetching ISS position …

Timestamp : 2026-02-21 15:00:02 UTC
Latitude  : -44.078508211233
Longitude : 85.535848675932

Reverse geocoding via Google Maps …

City      : Over ocean / unpopulated area
Country   : N/A
Address   : 4M77WGCP+H8

Google Maps link: https://www.google.com/maps?q=-44.078508211233,85.535848675932

── Distance from your location ──────────────────
Your city     : Calaca, Philippines
Your location : 13.995834, 120.826451
ISS location  : -44.078508211233, 85.535848675932
Distance      : 7,380.76 km

Record saved to iss_locations.db

No alert — ISS is 7,380.76 km away (threshold: 6.0 km)
```

## Requirements

- Python 3.9+
- Google Maps Geocoding API key ([enable it here](https://console.cloud.google.com/))

## Setup

**1. Clone or download the project**

```bash
cd "ISS Location"
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure your environment**

Create a `.env` file in the project root:

```
GOOGLE_MAPS_API_KEY=your_api_key_here
SMS_RECIPIENTS=+639567981777,+639181234567
PROXIMITY_THRESHOLD_KM=6
```

| Variable | Description |
|----------|-------------|
| `GOOGLE_MAPS_API_KEY` | Google Maps Geocoding API key |
| `SMS_RECIPIENTS` | Comma-separated phone numbers (with country code) |
| `PROXIMITY_THRESHOLD_KM` | Distance in km that triggers the SMS alert (default: 6) |

**5. Set your location**

Open `iss_tracker.py` and update these two lines with your coordinates:

```python
MY_LAT = 13.995834
MY_LNG = 120.826451
```

## Usage

**Track ISS position and save to database:**

```bash
python3 iss_tracker.py
```

**Launch the Streamlit dashboard:**

```bash
streamlit run dashboard.py
```

Then open **http://localhost:8501** in your browser.

## Dashboard

The Streamlit dashboard reads from the SQLite database and displays:

| Section | Details |
|---------|---------|
| **Metrics row** | Timestamp, latitude, longitude, city, distance from you |
| **Interactive map** | Real map with street, light, and satellite tile options |
| **🚀 Rocket marker** | Current ISS position |
| **🔵 Animated path** | Animated trail of all recorded ISS positions |
| **🏠 Home marker** | Your location |
| **╌ Dashed line** | Direct distance line from you to the ISS |
| **Clickable popups** | Timestamp, city, coordinates, and distance on each point |
| **Distance chart** | Line chart of ISS distance from you over time |
| **History table** | Full list of all saved records |

## Project Structure

```
ISS Location/
├── iss_tracker.py    # Main tracker script
├── dashboard.py      # Streamlit dashboard
├── iss_locations.db  # SQLite database (auto-created on first run)
├── requirements.txt  # Python dependencies
├── .env              # API key and config (not committed to version control)
└── README.md
```

## APIs Used

| API | Purpose | Auth |
|-----|---------|------|
| [wheretheiss.at](https://wheretheiss.at/w/developer) | Real-time ISS position | None (free) |
| [Google Maps Geocoding](https://developers.google.com/maps/documentation/geocoding) | Reverse geocode lat/lng to city | API key required |
| [Textbelt](https://textbelt.com) | SMS proximity alert | None (free tier: 1 SMS/day) |

## How Distance is Calculated

The script uses the **Haversine formula** to compute the great-circle distance between two points on Earth's surface, accounting for the curvature of the Earth. Note this is the surface distance — the ISS orbits at ~408 km altitude, so the actual straight-line distance is slightly greater.

## SMS Alert

When the ISS comes within the configured threshold (default 6 km), an SMS is sent to all numbers in `SMS_RECIPIENTS`. The message includes the ISS coordinates, your city, and a Google Maps link.

> **Note:** Textbelt free tier allows **1 SMS per day**. For unlimited SMS, purchase credits at [textbelt.com](https://textbelt.com) or switch to Twilio.
