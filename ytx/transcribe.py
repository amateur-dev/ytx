import os
import sys
import platform
import logging
from typing import List, Dict, Any, Tuple
from ytx.config import YtxConfig
from tqdm import tqdm
import pycountry

# Try to import mlx_whisper on Apple Silicon
try:
    if sys.platform == "darwin" and platform.machine() == "arm64":
        import mlx_whisper
        HAS_MLX = True
    else:
        HAS_MLX = False
except ImportError:
    HAS_MLX = False

if not HAS_MLX:
    import ctranslate2
    from faster_whisper import WhisperModel

# Suppress Hugging Face warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_WARNINGS"] = "1"
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

def get_language_name(code: str) -> str:
    """Convert a language code like 'en' or 'hi' to its full name."""
    try:
        lang = pycountry.languages.get(alpha_2=code.lower())
        if lang:
            return lang.name
    except Exception:
        pass
    return code

def transcribe_audio_mlx(audio_path: str, config: YtxConfig) -> Tuple[List[Dict[str, Any]], str]:
    """Transcribe using Apple Silicon MLX GPU acceleration."""
    # MLX uses specific repo IDs for models
    repo_map = {
        "tiny": "mlx-community/whisper-tiny",
        "base": "mlx-community/whisper-base",
        "small": "mlx-community/whisper-small",
        "medium": "mlx-community/whisper-medium",
        "large-v3": "mlx-community/whisper-large-v3"
    }
    repo_id = repo_map.get(config.model_size, "mlx-community/whisper-small")
    
    print(f"⚡ Using Apple Silicon MLX GPU acceleration!")
    print(f"📦 Loading Whisper AI model '{config.model_size}' into memory...")
    print(f"✍️  Transcribing audio to text... (This is incredibly fast on Mac GPU!)")
    
    decode_options = {}
    if config.source_lang:
        decode_options["language"] = config.source_lang
        
    original_stderr = sys.stderr
    if not config.verbose:
        sys.stderr = open(os.devnull, 'w')
        
    try:
        # MLX whisper is blocking but much faster
        result = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo=repo_id,
            verbose=config.verbose,
            **decode_options
        )
    finally:
        if not config.verbose:
            sys.stderr.close()
            sys.stderr = original_stderr
            
    detected_lang = result.get("language", config.source_lang or "en")
    lang_name = get_language_name(detected_lang)
    print(f"✅ Detected language: {lang_name}")
    
    result_segments = []
    for segment in result.get("segments", []):
        result_segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip()
        })
        
    return result_segments, detected_lang

def transcribe_audio_faster_whisper(audio_path: str, config: YtxConfig) -> Tuple[List[Dict[str, Any]], str]:
    """Transcribe using CPU/CUDA via faster-whisper."""
    print(f"📦 Loading Whisper AI model '{config.model_size}' into memory... (This might take a moment if downloading for the first time)")
    
    # Suppress ctranslate2 compute type warnings
    if not config.verbose:
        ctranslate2.set_log_level(logging.ERROR)
        
    original_stderr = sys.stderr
    if not config.verbose:
        sys.stderr = open(os.devnull, 'w')
        
    try:
        # device="auto" defaults to CUDA if available, else CPU.
        model = WhisperModel(config.model_size, device="auto", compute_type="default")
    finally:
        if not config.verbose:
            sys.stderr.close()
            sys.stderr = original_stderr
    
    print(f"🎙️  Analyzing audio file to detect spoken language...")
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language=config.source_lang,
        condition_on_previous_text=False
    )
    
    detected_lang = info.language
    lang_name = get_language_name(detected_lang)
    print(f"✅ Detected language: {lang_name} (Confidence: {info.language_probability:.0%})")
    
    result_segments = []
    total_duration = info.duration
    
    print(f"✍️  Transcribing audio to text...")
    with tqdm(total=total_duration, unit="s", unit_scale=True, bar_format="{l_bar}{bar}| {n_fmt}s/{total_fmt}s audio processed") as pbar:
        for segment in segments:
            result_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            pbar.update(segment.end - pbar.n)
            
            if config.verbose:
                tqdm.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
                
        if pbar.n < total_duration:
            pbar.update(total_duration - pbar.n)
            
    return result_segments, detected_lang

def transcribe_audio(audio_path: str, config: YtxConfig) -> Tuple[List[Dict[str, Any]], str]:
    """Route transcription to the best available backend."""
    if HAS_MLX:
        return transcribe_audio_mlx(audio_path, config)
    else:
        return transcribe_audio_faster_whisper(audio_path, config)
