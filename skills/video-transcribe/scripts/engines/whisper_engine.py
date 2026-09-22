import torch
from faster_whisper import WhisperModel
from typing import List, Dict, Any

def transcribe_whisper(file_path: str, model_size: str = "large-v3") -> List[Dict[str, Any]]:
    # Auto detect device
    if torch.cuda.is_available():
        device = "cuda"
        compute_type = "float16"
    else:
        device = "cpu"
        compute_type = "int8"
        
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception:
        # Fallback to medium
        model = WhisperModel("medium", device=device, compute_type=compute_type)
        
    segments, _ = model.transcribe(file_path)
    
    return [{"start": segment.start, "end": segment.end, "text": segment.text} for segment in segments]
