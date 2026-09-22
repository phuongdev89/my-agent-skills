import os
import httpx
from typing import List, Dict, Any

async def transcribe_groq(file_path: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Warning: GROQ_API_KEY is not set. Transcription may fail if authentication is required.")
        
    endpoint = os.getenv("GROQ_ENDPOINT_URL", "https://api.groq.com/openai/v1/audio/transcriptions")
    model = os.getenv("GROQ_MODEL")
    if not model:
        if "9router" in endpoint or "router" in endpoint:
            model = "groq/whisper-large-v3"
        else:
            model = "whisper-large-v3-turbo"
    
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else ""
    }
    
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
            data = {
                "model": model,
                "response_format": "verbose_json"
            }
            response = await client.post(endpoint, headers=headers, data=data, files=files, timeout=60)
            if response.status_code == 400 and "groq/" not in model:
                # Retry with groq/ prefix in case of proxy router
                data["model"] = f"groq/{model}"
                f.seek(0)
                files = {"file": (os.path.basename(file_path), f, "audio/mpeg")}
                response = await client.post(endpoint, headers=headers, data=data, files=files, timeout=60)
            
        response.raise_for_status()
        result = response.json()
        
        segments = result.get("segments", [])
        return [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in segments]
