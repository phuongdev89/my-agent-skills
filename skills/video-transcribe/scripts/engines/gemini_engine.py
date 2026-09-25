import os
import base64
import json
import httpx
from typing import List, Dict, Any

async def transcribe_gemini(file_path: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("GEMINI_TRANSCRIPTION_API_KEY") or os.getenv("GEMINI_TTS_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY is not set. Transcription will fail without an API key.")
        
    model = os.getenv("GEMINI_TRANSCRIPTION_MODEL", "").strip()
    if not model:
        raise RuntimeError("Thiếu GEMINI_TRANSCRIPTION_MODEL trong .env.")
    
    with open(file_path, "rb") as f:
        audio_data = f.read()
    b64_audio = base64.b64encode(audio_data).decode("utf-8")
    
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    prompt = "Please transcribe the following audio and provide the output as a JSON array of segments. Each segment should be an object with 'start' (start time in seconds as float), 'end' (end time in seconds as float), and 'text' (transcribed text). Example: [{\"start\": 0.0, \"end\": 2.5, \"text\": \"Hello world\"}]. Return ONLY valid JSON array without markdown backticks."
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "audio/mp3",
                        "data": b64_audio
                    }
                }
            ]
        }]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(endpoint, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            return json.loads(text)
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            return []
