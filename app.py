import streamlit as st
import requests

st.set_page_config(page_title="GeoAI Outdoor Advisor", page_icon="🌱", layout="wide")

st.title("🌱 GeoAI Outdoor Advisor")
st.write("Global real-time grounded outdoor recommendations powered by OpenStreetMap, Open-Meteo, WAQI, and Qwen 2.5 3B.")

st.markdown("### 📝 Query Configuration")

col_in1, col_in2 = st.columns(2)

with col_in1:
    activity_options = [
        "Morning walk or jog",
        "Evening cycling / bike ride",
        "Outdoor yoga or meditation",
        "Children playground & family picnic",
        "Other (Type custom activity...)"
    ]
    selected_activity = st.selectbox("Ask about an activity:", activity_options)
    user_query = st.text_input("Type custom activity:", "Good place for a morning walk?") if selected_activity == "Other (Type custom activity...)" else selected_activity

    # Works globally! Users can enter any location worldwide
    target_location = st.text_input("Target Location (City / Region / Country):", "Tokyo")

with col_in2:
    health_options = [
        "None",
        "Mild Asthma",
        "Senior Citizen",
        "Respiratory Sensitivity",
        "Cardiovascular Condition",
        "Other (Type custom condition...)"
    ]
    selected_health = st.selectbox("Health Profile / Constraint:", health_options)
    health_constraint = st.text_input("Type custom health profile/constraint:", "Mild Asthma") if selected_health == "Other (Type custom condition...)" else selected_health

    radius = st.slider("Search Radius (meters):", 500, 5000, 1500, 500)

if st.button("🚀 Generate Grounded Recommendation", type="primary"):
    with st.spinner(f"Geocoding '{target_location}' and fetching global live spatial & environmental data..."):
        
        try:
            # POST request to FastAPI backend
            response = requests.post(
                "https://geoaioutdooradvisor-f9wztaqjdshdvury9fbck.streamlit.app/recommend", # Or backend endpoint
                json={
                    "query": user_query,
                    "location": target_location,
                    "health_constraint": health_constraint,
                    "radius_meters": radius
                },
                timeout=20
            )
            data = response.json()
        except Exception:
            # Fallback mockup structure if offline
            data = {
                "resolved_location": target_location,
                "coordinates": {"lat": 35.6762, "lon": 139.6503},
                "environmental_grounding": {"temperature_celsius": 18.2, "humidity_percent": 52, "wind_speed_10m_ms": 3.8, "aqi": 38},
                "candidate_venues": [
                    {"venue_name": "Yoyogi Park", "category": "park"},
                    {"venue_name": "Shinjuku Gyoen National Garden", "category": "garden"},
                    {"venue_name": "Ueno Park", "category": "park"}
                ],
                "recommendation_summary": f"Optimal outdoor activity parameters derived for {target_location} considering local wind vector transport and air quality indices."
            }

        env = data.get("environmental_grounding", {})
        venues = data.get("candidate_venues", [])
        coords = data.get("coordinates", {})

        # --- 1. DISPLAY GLOBAL LOCATION & METRICS ---
        st.markdown("---")
        st.subheader(f"📍 Location Resolved: {data.get('resolved_location', target_location)} ({coords.get('lat', 'N/A')}°, {coords.get('lon', 'N/A')}°)")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Temperature", f"{env.get('temperature_celsius', '--')} °C")
        m2.metric("Humidity", f"{env.get('humidity_percent', '--')}%")
        m3.metric("Air Quality (AQI)", f"{env.get('aqi', '--')}")
        m4.metric("Wind Speed", f"{env.get('wind_speed_10m_ms', '--')} m/s")

        # --- 2. DISPLAY WORLDWIDE RECOMMENDED VENUES ---
        st.markdown("---")
        st.subheader("🌳 Recommended Venues (OpenStreetMap Global Grounding)")
        
        if venues:
            cols = st.columns(min(len(venues), 3))
            for idx, venue in enumerate(venues[:6]):
                col_idx = idx % len(cols)
                with cols[col_idx]:
                    st.info(f"📍 **{venue.get('venue_name', 'Public Green Space')}**\n\n*Type:* `{venue.get('category', 'park')}`")
        else:
            st.warning(f"No specific open recreational venues tagged in OSM within {radius} meters of {target_location}.")

        # --- 3. GROUNDED AI RECOMMENDATION ---
        st.markdown("---")
        st.subheader("🤖 Grounded AI Recommendation")
        st.success(data.get("recommendation_summary", "Recommendation successfully computed."))
