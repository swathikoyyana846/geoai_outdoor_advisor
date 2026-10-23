import streamlit as st
import json

st.set_page_config(page_title="GeoAI Outdoor Advisor", page_icon="🌤️")

st.title("🌤️ GeoAI Outdoor Advisor")
st.write("Welcome to the GeoAI Outdoor Advisor API Service!")

# Load sample payload if available
try:
    with open("member2_payload.json", "r") as f:
        payload = json.load(f)
    st.subheader("📋 Sample Payload Data")
    st.json(payload)
except Exception as e:
    st.info("API Service is live and active.")

st.success("✅ Service Status: Running Active")
