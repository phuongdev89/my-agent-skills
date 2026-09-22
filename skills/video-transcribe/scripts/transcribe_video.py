import argparse
import os
import sys
import asyncio
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Fix sys.path for internal imports
scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try importing utils and engines
try:
    from utils.ytdlp_helper import download_media
    from utils.audio_prep import extract_audio_as_mp3
    from utils.subtitle_exporters import export_all_subtitles
except ImportError:
    print("Could not import utils. Make sure they exist.")

try:
    from engines.whisper_engine import transcribe_whisper
    from engines.groq_engine import transcribe_groq
    from engines.gemini_engine import transcribe_gemini
except ImportError:
    transcribe_whisper = None
    transcribe_groq = None
    transcribe_gemini = None

def interactive_selection():
    print("Select transcription method:")
    print("1. groq (Ultra fast, cloud based)")
    print("2. whisper (faster-whisper, offline, secure)")
    print("3. gemini (Deep analysis, cloud based)")
    choice = input("Enter choice (1/2/3): ")
    if choice == '1': return 'groq'
    elif choice == '2': return 'whisper'
    elif choice == '3': return 'gemini'
    return 'whisper'

def print_timeline(segments):
    for seg in segments:
        start = seg.get('start', 0)
        end = seg.get('end', 0)
        text = seg.get('text', '')
        # Convert seconds to HH:MM:SS.mmm
        start_ms = int((start % 1) * 1000)
        start_s = int(start)
        start_str = f"{start_s // 3600:02d}:{(start_s % 3600) // 60:02d}:{start_s % 60:02d}.{start_ms:03d}"
        
        end_ms = int((end % 1) * 1000)
        end_s = int(end)
        end_str = f"{end_s // 3600:02d}:{(end_s % 3600) // 60:02d}:{end_s % 60:02d}.{end_ms:03d}"
        
        print(f"[{start_str} --> {end_str}] {text}")

import datetime
import shutil

async def run_transcription(args):
    method = args.method
    if method == "interactive":
        method = interactive_selection()
        
    # Setup directories
    if args.session_dir:
        session_dir = Path(args.session_dir).resolve()
    else:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        session_dir = Path(f"./scratch/{today}_video-transcribe_default").resolve()
        
    temp_dir = session_dir / "temp"
    output_dir = session_dir / "output"
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
        
    print(f"Preparing media for transcription...")
    
    input_path = args.input
    is_temp_file = False
    
    if input_path.startswith("http"):
        print("Downloading media...")
        temp_path = str(temp_dir / "downloaded_media.mp4")
        input_path = download_media(input_path, temp_path)
        is_temp_file = True
    
    audio_path = input_path
    # If input is a video file, extract audio
    if any(input_path.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.mov', '.avi']):
        print("Extracting audio from video...")
        audio_path = str(temp_dir / "temp_audio.mp3")
        extract_audio_as_mp3(input_path, audio_path)
        is_temp_file = True

    print(f"\nUsing method: {method}")
    segments = []
    used_model = "unknown"
    start_time = time.time()
    
    if method == "whisper":
        if transcribe_whisper:
            segments = transcribe_whisper(audio_path)
        used_model = "large-v3 (or fallback)"
    elif method == "groq":
        if transcribe_groq:
            segments = await transcribe_groq(audio_path)
        used_model = "whisper-large-v3-turbo"
    elif method == "gemini":
        if transcribe_gemini:
            segments = await transcribe_gemini(audio_path)
        used_model = "gemini-2.5-flash"
    
    elapsed_time = time.time() - start_time
    
    print(f"\nPhương thức đã dùng: {method} | Model: {used_model} | Thời lượng xử lý: {elapsed_time:.2f}s")
    
    print("\n--- Transcription Timeline ---")
    print_timeline(segments)
    
    print("\nExporting files...")
    base_name = str(output_dir / "transcription")
    export_all_subtitles(segments, base_name)
    print(f"Exported to {base_name}.[srt|vtt|txt|json]")
    
    # Cleanup temp files
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Could not remove temp dir: {e}")

def main():
    parser = argparse.ArgumentParser(description="Transcribe video/audio")
    parser.add_argument("--input", required=True, help="Input file path or URL")
    parser.add_argument("--method", choices=["groq", "whisper", "gemini", "interactive"], default="interactive")
    parser.add_argument("--session-dir", type=Path, help="Directory to save session data")
    
    args = parser.parse_args()
    asyncio.run(run_transcription(args))

if __name__ == "__main__":
    main()
