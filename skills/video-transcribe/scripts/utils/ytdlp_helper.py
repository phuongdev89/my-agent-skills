import yt_dlp
import os

def download_media(url: str, output_path: str) -> str:
    """Download video/audio using yt-dlp"""
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestaudio/best',
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            return output_path
        except Exception as e:
            print(f"Error downloading with yt-dlp: {e}")
            return ""
