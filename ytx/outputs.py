import os
import re
import json
from typing import Dict, Any

def sanitize_filename(name: str) -> str:
    """Remove illegal characters for directory/file names."""
    # Replace anything that isn't alphanumeric, space, dot, dash, or underscore with underscore
    name = re.sub(r'[^\w\s\.-]', '_', name)
    return name.strip()

def prepare_output_dir(base_dir: str, video_title: str) -> str:
    """Create and return the path to the video's specific output directory."""
    safe_title = sanitize_filename(video_title)
    if not safe_title:
        safe_title = "unknown_video"
    out_dir = os.path.join(base_dir, safe_title)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def save_info_json(info: Dict[str, Any], output_dir: str) -> str:
    filepath = os.path.join(output_dir, "source.info.json")
    with open(filepath, "w", encoding="utf-8") as f:
        # Extract only a subset of info to save space, or just dump it all.
        # It's usually big, so maybe a subset.
        subset = {
            "id": info.get("id"),
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "duration": info.get("duration"),
            "view_count": info.get("view_count"),
        }
        json.dump(subset, f, indent=2, ensure_ascii=False)
    return filepath

def get_base_filepath(output_dir: str, prefix: str) -> str:
    """Generate the base prefix for files, e.g. output/title/source.transcribed"""
    return os.path.join(output_dir, f"source.{prefix}")
    
def cleanup_audio(audio_path: str, keep_audio: bool) -> None:
    if not keep_audio and audio_path and os.path.exists(audio_path):
        os.remove(audio_path)
