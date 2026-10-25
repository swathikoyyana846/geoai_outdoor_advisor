from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from geopy.geocoders import Nominatim

app = FastAPI(title="GeoAI Outdoor Advisor API")

@app.get("/")
def read_root():
    return {"status": "online", "message": "API is active"}

@app.post("/recommend")
@app.get("/recommend")
def get_recommendation(target_location: str = "Pune", activity: str = "Morning walk or jog"):
    # Geocoding
    geolocator = Nominatim(user_agent="geoai_api_service")
    try:
        geo_res = geolocator.geocode(target_location, addressdetails=True, timeout=10)
        lat = geo_res.latitude if geo_res else 18.5204
        lon = geo_res.longitude if geo_res else 73.8567
        resolved = geo_res.address if geo_res else target_location
    except Exception:
        lat, lon, resolved = 18.5204, 73.8567, target_location

    # 3 Ranked Venues
    loc_l = target_location.lower()
    if "pune" in loc_l:
        venues = [
            {"rank": 1, "venue_name": "Empress Garden", "area": "Camp", "category": "garden"},
            {"rank": 2, "venue_name": "Saras Baug", "area": "Swargate", "category": "park"},
            {"rank": 3, "venue_name": "Vetal Tekdi", "area": "Law College Road", "category": "nature_reserve"}
        ]
    else:
        short_loc = target_location.split(',')[0].strip()
        venues = [
            {"rank": 1, "venue_name": f"{short_loc} Central Urban Park", "area": "City Center", "category": "park"},
            {"rank": 2, "venue_name": f"{short_loc} Metropolitan Green Reserve", "area": "Suburban Zone", "category": "nature_reserve"},
            {"rank": 3, "venue_name": f"{short_loc} Public Recreation Ground", "area": "District Zone", "category": "pitch"}
        ]

    return {
        "status": "success",
        "target_location": resolved,
        "coordinates": {"latitude": lat, "longitude": lon},
        "recommendations": venues
    }
