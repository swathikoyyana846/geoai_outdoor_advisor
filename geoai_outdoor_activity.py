

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "Qwen/Qwen2.5-3B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto"
)
print("Qwen 2.5 3B Model loaded successfully!")

import json
from datetime import datetime
from geopy.geocoders import Nominatim
import requests
import requests_cache

# 1. Cache setup from friend's code
requests_cache.install_cache('geo_weather_cache', backend='sqlite', expire_after=3600)
MASTER_DB_FILENAME = 'geospatial_knowledge_base.json'

# --- FRIEND'S PIPELINE CLASS ---
class DynamicGeoPipeline:
    def __init__(self, user_place_name, search_radius_meters=2500):
        self.place_name = user_place_name.lower().strip()
        self.radius = search_radius_meters
        self.lat = None
        self.lon = None
        self.venues = []

    def get_coordinates(self):
        geolocator = Nominatim(user_agent="geo_ai_hackathon_colab_v2")
        location = geolocator.geocode(self.place_name)
        if location:
            self.lat = location.latitude
            self.lon = location.longitude
            return True
        return False

    def fetch_nearby_venues(self, top_n=8):
        overpass_url = "https://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["leisure"](around:{self.radius},{self.lat},{self.lon});
          way["leisure"](around:{self.radius},{self.lat},{self.lon});
          node["boundary"="protected_area"](around:{self.radius},{self.lat},{self.lon});
        );
        out body;
        >;
        out skel qt;
        """
        headers = {'User-Agent': 'GeoAIHackathonPipeline/1.0'}
        try:
            response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=20)
            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                count = 0
                for el in elements:
                    if 'tags' in el and 'name' in el['tags']:
                        v_lat = el.get('lat') or (el.get('center', {}).get('lat') if 'center' in el else None)
                        v_lon = el.get('lon') or (el.get('center', {}).get('lon') if 'center' in el else None)
                        if v_lat and v_lon:
                            self.venues.append({
                                "id": el.get('id'),
                                "name": el['tags']['name'],
                                "type": el['tags'].get('leisure', 'park/ground'),
                                "lat": v_lat,
                                "lon": v_lon
                            })
                            count += 1
                            if count >= top_n:
                                break
        except Exception as e:
            print(f"[-] Overpass fetch warning: {e}")

    def fetch_weather_and_aqi(self, waqi_token="demo"):
        enriched_venues = []
        for venue in self.venues:
            v_lat, v_lon = venue['lat'], venue['lon']
            # Open-Meteo API
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={v_lat}&longitude={v_lon}&current=temperature_2m,relative_humidity_2m,rain,wind_speed_10m,wind_direction_10m"
            try:
                w_resp = requests.get(w_url, timeout=10)
                weather_data = w_resp.json().get('current', {}) if w_resp.status_code == 200 else {}
            except Exception:
                weather_data = {}

            # WAQI API
            a_url = f"https://api.waqi.info/feed/geo:{v_lat};{v_lon}/?token={waqi_token}"
            try:
                a_resp = requests.get(a_url, timeout=10)
                aqi_data = a_resp.json().get('data', {}) if a_resp.status_code == 200 else {}
                aqi_val = aqi_data.get('aqi', 'N/A')
            except Exception:
                aqi_val = 'N/A'

            wind_dir = weather_data.get('wind_direction_10m', 0)
            wind_speed = weather_data.get('wind_speed_10m', 0.0)
            pollution_flag = False
            pollution_note = "Clean air expected from current wind vector."
            if 270 <= wind_dir <= 360 and wind_speed > 5.0:
                pollution_flag = True
                pollution_note = "WARNING: Wind vector aligns with industrial/traffic corridor."

            venue_record = {
                "venue_id": venue['id'],
                "venue_name": venue['name'],
                "category": venue['type'],
                "coordinates": {"lat": v_lat, "lon": v_lon},
                "live_weather": {
                    "temperature_c": weather_data.get('temperature_2m', 28.0),
                    "humidity_pct": weather_data.get('relative_humidity_2m', 60),
                    "rain_mm": weather_data.get('rain', 0.0),
                    "wind_speed_kmh": wind_speed,
                    "wind_direction_deg": wind_dir
                },
                "air_quality": {
                    "aqi": aqi_val,
                    "status": "Good" if isinstance(aqi_val, int) and aqi_val <= 50 else "Moderate/Poor"
                },
                "pollution_analysis": {
                    "hazard_flag": pollution_flag,
                    "reason": pollution_note
                }
            }
            enriched_venues.append(venue_record)
        self.venues = enriched_venues

    def build_slm_context(self):
        context_lines = [
            f"Target Location: {self.place_name} (Lat: {self.lat}, Lon: {self.lon}).",
            "Available sports venues, parks, and grounds with live atmospheric data:"
        ]
        for v in self.venues:
            w = v['live_weather']
            a = v['air_quality']
            p = v['pollution_analysis']
            line = (
                f"- Venue: {v['venue_name']} ({v['category']}) | Temp: {w['temperature_c']}°C, "
                f"Humidity: {w['humidity_pct']}%, Rain: {w['rain_mm']}mm, Wind: {w['wind_speed_kmh']} km/h at {w['wind_direction_deg']}° | "
                f"AQI: {a['aqi']} ({a['status']}) | Pollution Alert: {p['hazard_flag']} - {p['reason']}"
            )
            context_lines.append(line)
        return "\n".join(context_lines)

# --- FRIEND'S GET OR FETCH FUNCTION ---
def get_or_fetch_place_data(user_requested_place):
    clean_name = user_requested_place.lower().strip()
    try:
        with open(MASTER_DB_FILENAME, 'r', encoding='utf-8') as f:
            master_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        master_data = {}

    if clean_name in master_data:
        print(f"[+] Loaded '{clean_name}' instantly from JSON Master Knowledge Base.")
        return master_data[clean_name]['slm_text_context'], True

    print(f"[*] New location requested ('{clean_name}'). Fetching live data via pipeline...")
    pipeline = DynamicGeoPipeline(clean_name, search_radius_meters=3000)
    if pipeline.get_coordinates():
        pipeline.fetch_nearby_venues(top_n=8)
        pipeline.fetch_weather_and_aqi(waqi_token="demo")
        slm_text = pipeline.build_slm_context()

        master_data[clean_name] = {
            "metadata": {"lat": pipeline.lat, "lon": pipeline.lon, "timestamp": datetime.utcnow().isoformat() + "Z"},
            "slm_text_context": slm_text,
            "candidate_venues": pipeline.venues
        }
        with open(MASTER_DB_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=4, ensure_ascii=False)
        return slm_text, True
    else:
        return f"Sorry, could not find coordinates for location '{user_requested_place}'.", False


# =======================================================
#  TWO-STAGE SLM ENGINE (BACKGROUND + MAIN SLM)
# =======================================================

# 1. Background SLM: Query Parser (Extracts Place, Health, Activity)
def parse_query_with_background_slm(user_query: str) -> dict:
    parser_system = (
        "You are an NLP query parser. Analyze the user question and return a valid JSON object ONLY. "
        "Keys must be: 'location' (neighborhood or city name only, null if missing), "
        "'activity' (e.g., running, walk, cricket), 'health_condition' (e.g., asthma, elderly, none). "
        "Do not write explanations, return ONLY the JSON block."
    )
    messages = [
        {"role": "system", "content": parser_system},
        {"role": "user", "content": f"Parse this query: \"{user_query}\""}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=80, temperature=0.1)

    parsed_text = tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()

    # Clean json output
    try:
        # Extract json portion if wrapped in markdown
        if "{" in parsed_text and "}" in parsed_text:
            json_str = parsed_text[parsed_text.find("{"):parsed_text.rfind("}")+1]
            return json.loads(json_str)
    except Exception:
        pass
    return {"location": None, "activity": "outdoor activity", "health_condition": "none"}


# 2. Main SLM: Grounded Outdoor Advisor
def run_main_advisor_slm(user_query: str, live_geo_context: str, parsed_info: dict) -> str:
    system_instruction = (
        "You are an expert GeoAI outdoor advisor. Strictly reason over the provided live data. "
        "Do NOT invent or hallucinate places, temperature, or AQI numbers. "
        "Give your final advice in these clear sections:\n"
        "1. Best Recommended Venue & Ideal Time\n"
        "2. Grounded Justification (Quote live weather, wind direction & AQI numbers)\n"
        "3. Practical Advice (What to carry, what to watch for, considering user health profile)\n"
        "4. Times or Locations to Avoid\n"
        "5. Data Sources Used"
    )

    user_prompt = (
        f"User Query: {user_query}\n"
        f"Extracted Profile: Activity={parsed_info.get('activity')}, Health={parsed_info.get('health_condition')}\n\n"
        f"Live Context Data:\n{live_geo_context}"
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=450, temperature=0.2, do_sample=True, top_p=0.9)
    return tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)


# =======================================================
# MASTER CONTROLLER: END-TO-END ASSISTANT
# =======================================================
def geoai_assistant(user_query: str):
    print("=" * 60)
    print(f"USER QUERY: {user_query}")
    print("=" * 60)

    # Step 1: Background SLM runs to parse question
    print("[1/3] Background SLM: Extracting location and personal details...")
    parsed = parse_query_with_background_slm(user_query)
    target_location = parsed.get("location")
    print(f"      -> Extracted Entities: {parsed}")

    if not target_location or target_location.lower() == "null":
        return "Clarification Needed: Please specify the location or city where you are planning this outdoor activity."

    # Step 2: Friend's Dynamic Pipeline runs for that specific location
    print(f"[2/3] Pipeline: Checking knowledge base or fetching live data for '{target_location}'...")
    geo_context, success = get_or_fetch_place_data(target_location)

    if not success:
        return geo_context  # Returns coordinate failure message

    # Step 3: Main SLM runs to generate the final decision
    print("[3/3] Main SLM: Reasoning over live spatial context and generating grounded recommendation...")
    final_response = run_main_advisor_slm(user_query, geo_context, parsed)
    return final_response

# Test 1: Powai Asthma Case (from Rulebook)
print(geoai_assistant("I have mild asthma, where's good for a morning walk near japan in the next two days?"))
