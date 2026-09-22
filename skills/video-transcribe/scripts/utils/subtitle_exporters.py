import json
from typing import List, Dict, Any

def format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def format_time_vtt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def export_srt(segments: List[Dict[str, Any]], filepath: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            start = format_time(seg.get('start', 0))
            end = format_time(seg.get('end', 0))
            f.write(f"{i}\n{start} --> {end}\n{seg.get('text', '').strip()}\n\n")

def export_vtt(segments: List[Dict[str, Any]], filepath: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            start = format_time_vtt(seg.get('start', 0))
            end = format_time_vtt(seg.get('end', 0))
            f.write(f"{start} --> {end}\n{seg.get('text', '').strip()}\n\n")

def export_txt(segments: List[Dict[str, Any]], filepath: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        for seg in segments:
            f.write(f"{seg.get('text', '').strip()}\n")

def export_json(segments: List[Dict[str, Any]], filepath: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

def export_all_subtitles(segments: List[Dict[str, Any]], base_path: str):
    export_srt(segments, f"{base_path}.srt")
    export_vtt(segments, f"{base_path}.vtt")
    export_txt(segments, f"{base_path}.txt")
    export_json(segments, f"{base_path}.json")

