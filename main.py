from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Member 1 & Member 2 files nunchi functions import chestunnam
from geoai_outdoor_activity import parse_query_with_background_slm, get_or_fetch_place_data
from model_reasoning import generate_recommendation

app = FastAPI(
    title="GeoAI Outdoor Advisor API", 
    description="API for recommending outdoor venues based on live weather, AQI, and user health profiles.",
    version="1.0"
)

class QueryRequest(BaseModel):
    query: str

@app.post("/recommend")
def recommend_venue(req: QueryRequest):
    try:
        # 1. Background SLM: Query parse chesi location extract chestundi
        parsed = parse_query_with_background_slm(req.query)
        target_location = parsed.get("location")
        
        if not target_location or str(target_location).lower() == "null":
            return {"error": "Please specify the location or city in your query."}

        # 2. Pipeline: Live weather, AQI & venues data fetch chestundi
        geo_context, success = get_or_fetch_place_data(target_location)
        if not success:
            return {"error": geo_context}

        # 3. Main Reasoning Model: Live data tho grounded recommendation generate chestundi
        final_response = generate_recommendation(req.query, geo_context)
        
        return {
            "query": req.query,
            "parsed_info": parsed,
            "recommendation": final_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"status": "GeoAI API is running successfully!"}