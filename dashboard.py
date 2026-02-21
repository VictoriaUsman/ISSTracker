"""
ISS Location Tracker — Streamlit Dashboard
Reads historical ISS positions from SQLite and visualizes them.
"""

import sqlite3
import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
from folium.plugins import AntPath

DB_PATH = "iss_locations.db"
MY_LAT  = 13.995834
MY_LNG  = 120.826451

st.set_page_config(
    page_title="ISS Location Tracker",
    page_icon="🛸",
    layout="wide",
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def load_data() -> pd.DataFrame:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(
                "SELECT * FROM iss_locations ORDER BY timestamp DESC",
                conn,
            )
        return df
    except Exception:
        return pd.DataFrame()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🛸 ISS Location Tracker")
st.caption("Live history of the International Space Station — powered by wheretheiss.at & Google Maps")

col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()

df = load_data()

if df.empty:
    st.warning("No data yet. Run `python3 iss_tracker.py` first to populate the database.")
    st.stop()

latest = df.iloc[0]

# ── Metrics row ───────────────────────────────────────────────────────────────
st.subheader("Latest Position")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Timestamp",  latest["timestamp"])
m2.metric("Latitude",   f"{latest['latitude']:.4f}°")
m3.metric("Longitude",  f"{latest['longitude']:.4f}°")
m4.metric("City",       f"{latest['city']}, {latest['country']}")
m5.metric("Distance from You", f"{latest['distance_km']:,.2f} km")

st.divider()

# ── Map ───────────────────────────────────────────────────────────────────────
st.subheader("ISS Path Map")

m = folium.Map(
    location=[latest["latitude"], latest["longitude"]],
    zoom_start=2,
    tiles="CartoDB positron",
)

# Tile layer switcher
folium.TileLayer("OpenStreetMap",  name="Street Map").add_to(m)
folium.TileLayer("CartoDB positron", name="Light").add_to(m)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
    name="Satellite",
).add_to(m)

# Animated flight path (oldest → newest)
coords_asc = df[["latitude", "longitude"]].iloc[::-1].values.tolist()
if len(coords_asc) > 1:
    AntPath(
        locations=coords_asc,
        color="#1E90FF",
        weight=3,
        opacity=0.8,
        delay=800,
    ).add_to(m)

# Historical positions (blue circles)
for _, row in df.iloc[1:].iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=5,
        color="#1E90FF",
        fill=True,
        fill_opacity=0.6,
        popup=folium.Popup(
            f"<b>{row['city']}, {row['country']}</b><br>"
            f"🕐 {row['timestamp']}<br>"
            f"📍 {row['latitude']:.4f}, {row['longitude']:.4f}<br>"
            f"📏 {row['distance_km']:,.2f} km from you",
            max_width=220,
        ),
    ).add_to(m)

# Current ISS position (orange rocket marker)
folium.Marker(
    location=[latest["latitude"], latest["longitude"]],
    popup=folium.Popup(
        f"<b>🛸 ISS — Current Position</b><br>"
        f"📍 {latest['latitude']:.4f}, {latest['longitude']:.4f}<br>"
        f"🌍 {latest['city']}, {latest['country']}<br>"
        f"🕐 {latest['timestamp']}<br>"
        f"📏 {latest['distance_km']:,.2f} km from you",
        max_width=240,
    ),
    tooltip="🛸 ISS (current)",
    icon=folium.Icon(color="orange", icon="rocket", prefix="fa"),
).add_to(m)

# Your location (green marker)
folium.Marker(
    location=[MY_LAT, MY_LNG],
    popup=folium.Popup(
        "<b>📍 Your Location</b><br>Calaca, Philippines",
        max_width=180,
    ),
    tooltip="Your location",
    icon=folium.Icon(color="green", icon="home", prefix="fa"),
).add_to(m)

# Distance line between you and ISS
folium.PolyLine(
    locations=[[MY_LAT, MY_LNG], [latest["latitude"], latest["longitude"]]],
    color="red",
    weight=1.5,
    dash_array="6",
    opacity=0.5,
    tooltip=f"Distance: {latest['distance_km']:,.2f} km",
).add_to(m)

folium.LayerControl().add_to(m)

st_folium(m, use_container_width=True, height=520, returned_objects=[])

st.caption("🚀 Current ISS position   🔵 Previous positions   🏠 Your location (Calaca, Philippines)   ╌ Distance line")

st.divider()

# ── Distance chart ────────────────────────────────────────────────────────────
st.subheader("Distance from Your Location Over Time")
chart_df = df[["timestamp", "distance_km"]].iloc[::-1].reset_index(drop=True)
chart_df = chart_df.rename(columns={"timestamp": "Timestamp", "distance_km": "Distance (km)"})
st.line_chart(chart_df.set_index("Timestamp"))

st.divider()

# ── History table ─────────────────────────────────────────────────────────────
st.subheader(f"Location History ({len(df)} records)")
st.dataframe(
    df[["timestamp", "latitude", "longitude", "city", "country", "distance_km"]].rename(columns={
        "timestamp":   "Timestamp",
        "latitude":    "Latitude",
        "longitude":   "Longitude",
        "city":        "City",
        "country":     "Country",
        "distance_km": "Distance (km)",
    }),
    use_container_width=True,
    hide_index=True,
)
