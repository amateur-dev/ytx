import json
from typing import List, Dict, Any

def _format_timestamp(seconds: float, is_srt: bool = True) -> str:
    """Format seconds into SRT or VTT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    
    if is_srt:
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    else:
        # VTT format
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
        else:
            return f"{minutes:02d}:{secs:02d}.{millis:03d}"

def write_srt(segments: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = _format_timestamp(seg["start"], is_srt=True)
            end = _format_timestamp(seg["end"], is_srt=True)
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{seg['text']}\n\n")

def write_vtt(segments: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            start = _format_timestamp(seg["start"], is_srt=False)
            end = _format_timestamp(seg["end"], is_srt=False)
            f.write(f"{start} --> {end}\n")
            f.write(f"{seg['text']}\n\n")

def write_txt(segments: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"{seg['text']}\n")

def write_json(segments: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

def write_format(segments: List[Dict[str, Any]], filepath: str, format_type: str) -> None:
    """Dispatches to the correct writer based on format_type."""
    if format_type == "srt":
        write_srt(segments, filepath)
    elif format_type == "vtt":
        write_vtt(segments, filepath)
    elif format_type == "txt":
        write_txt(segments, filepath)
    elif format_type == "json":
        write_json(segments, filepath)
    else:
        raise ValueError(f"Unsupported format: {format_type}")
