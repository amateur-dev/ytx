import os
import yt_dlp
from typing import Dict, Any, Optional
from ytx.config import YtxConfig

def get_video_info(url: str, config: YtxConfig) -> Dict[str, Any]:
    """Fetch video metadata and subtitle information using yt-dlp."""
    ydl_opts = {
        'quiet': not config.verbose,
        'no_warnings': not config.verbose,
        'extract_flat': False, # Need full metadata for subs
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        if config.verbose:
            print(f"Exception during metadata extraction: {e}")
        return {}

def download_audio(url: str, output_path_base: str, config: YtxConfig) -> Optional[str]:
    """Download audio using yt-dlp and ffmpeg to a specific base path.
    Returns the path to the extracted audio file.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': not config.verbose,
        'no_warnings': not config.verbose,
        'outtmpl': f"{output_path_base}.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav', # wav or mp3 is fine, wav is good for whisper
            'preferredquality': '192',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download([url])
            if error_code != 0:
                print(f"Error downloading audio for {url}")
                return None
            return f"{output_path_base}.wav"
    except Exception as e:
        print(f"Exception during audio download: {e}")
        return None
