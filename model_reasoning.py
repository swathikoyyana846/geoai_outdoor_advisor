```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"

# Initialize model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto"
)

def generate_recommendation(user_query: str, live_geo_data: str) -> str:
    system_instruction = (
        "You are an expert GeoAI outdoor advisor. "
        "Strictly reason over the provided live data. "
        "Do NOT invent or hallucinate any weather, AQI values, or venue names. "
        "Support your recommendation with live numbers (temperature, wind, AQI). "
        "Provide your answer with the following clear structure:\n"
        "1. Recommended Venue & Best Time Slot\n"
        "2. Justification (Why this place and hour? Account for wind/air quality)\n"
        "3. Practical Advice (What to carry, what to watch out for)\n"
        "4. Times or Places to Avoid (and reason why)\n"
        "5. Data Sources Used"
    )

    user_content = f"User Request: {user_query}\n\nLive Context Data:\n{live_geo_data}"

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_content}
    ]

    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_new_tokens=450,
            temperature=0.2,
            do_sample=True,
            top_p=0.9
        )

    response = tokenizer.decode(output_tokens[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response