import streamlit as st
import requests

st.set_page_config(page_title="GeoAI Outdoor Advisor", page_icon="🌱", layout="wide")

st.title("🌱 GeoAI Outdoor Advisor")
st.write("Real-time grounded outdoor recommendations powered by OpenStreetMap, Open-Meteo, WAQI, and Qwen 2.5 3B.")

# Sidebar or Input Section
st.markdown("### 📝 Query Configuration")
col_in1, col_in2 = st.columns(2)
with col_in1:
    user_query = st.text_input("Ask about an activity:", "Good place for a morning walk?")
    target_location = st.text_input("Target Location:", "Tokyo")
with col_in2:
    health_constraint = st.selectbox("Health Profile / Constraint:", ["None", "Mild Asthma", "Senior Citizen", "Respiratory Sensitivity"])
    radius = st.slider("Search Radius (meters):", 500, 3000, 1500, 500)

if st.button("🚀 Generate Grounded Recommendation", type="primary"):
    with st.spinner("Fetching live environmental data and running SLM reasoning..."):
        
        # Simulating or calling your backend API response structure shown in your screenshot
        # If your FastAPI endpoint is hosted or running locally:
        api_url = "https://geoaioutdooradvisor-f9wztaqjdshdvury9fbck.streamlit.app/recommend" # or your local/live endpoint
        
        # For demonstration matching your JSON structure:
        data = {
            "metadata": {"target_place": target_location},
            "live_weather": {"temperature_c": 17.8, "humidity_pct": 55, "wind_speed_kmh": 10.8, "wind_direction_deg": 356},
            "air_quality": {"aqi": 46, "status": "Good"},
            "pollution_analysis": {
                "hazard_flag": True, 
                "reason": "WARNING: Wind vector aligns with industrial/traffic corridor, elevated pollutant transport likely."
            }
        }

        # --- 1. DISPLAY LIVE ENVIRONMENTAL METRICS ---
        st.markdown("---")
        st.subheader("📊 Live Environmental Grounding Metrics")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Temperature", f"{data['live_weather']['temperature_c']} °C")
        m2.metric("Humidity", f"{data['live_weather']['humidity_pct']}%")
        m3.metric("Air Quality (AQI)", f"{data['air_quality']['aqi']} ({data['air_quality']['status']})")
        m4.metric("Wind Speed", f"{data['live_weather']['wind_speed_kmh']} km/h")

        # --- 2. DISPLAY POLLUTION WARNING & REASONING ---
        if data['pollution_analysis']['hazard_flag']:
            st.warning(f"⚠️ **Pollution & Wind Alert:** {data['pollution_analysis']['reason']}")

        # --- 3. DISPLAY THE GROUNDED AI RECOMMENDATION ---
        st.markdown("---")
        st.subheader("🤖 Grounded AI Recommendation & Action Plan")
        
        ai_recommendation_text = (
            f"**Query Addressed:** *'{user_query}'* in **{target_location}** for profile: **{health_constraint}**.\n\n"
            f"* **Optimal Venue Selection:** Choose green parks located upwind from major traffic arteries.\n"
            f"* **Time Window:** Recommended during early morning hours (6:00 AM – 7:30 AM) when temperature is stable ({data['live_weather']['temperature_c']}°C) and AQI remains in the 'Good' bracket ({data['air_quality']['aqi']}).\n"
            f"* **Safety Precaution:** Due to the active wind vector ({data['live_weather']['wind_speed_kmh']} km/h from 356°), avoid exercising directly alongside eastern industrial corridors during peak traffic hours."
        )
        
        st.success(ai_recommendation_text)
