import subprocess
import os

def extract_audio_as_mp3(video_path: str, output_path: str) -> bool:
    """Extract audio from video to mp3 (mono, 64k bitrate)"""
    try:
        command = [
            "ffmpeg",
            "-i", video_path,
            "-vn",          # No video
            "-ac", "1",     # Mono channel
            "-b:a", "64k",  # 64k bitrate
            "-y",           # Overwrite output
            output_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e}")
        return False
