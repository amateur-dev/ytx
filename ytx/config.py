from dataclasses import dataclass
from typing import Optional, List

@dataclass
class YtxConfig:
    urls: List[str]
    official_only: bool = False
    allow_auto_subs: bool = False
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None  # '--to'
    output_format: str = "srt"  # srt, vtt, txt, json
    model_size: str = "small" # tiny, base, small, medium, large-v3
    output_dir: str = "output"
    keep_audio: bool = False
    verbose: bool = False
