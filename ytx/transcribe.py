import os
import sys
import logging
import ctranslate2
from typing import List, Dict, Any, Tuple
from faster_whisper import WhisperModel
from ytx.config import YtxConfig
from tqdm import tqdm
import pycountry

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

def transcribe_audio(audio_path: str, config: YtxConfig) -> Tuple[List[Dict[str, Any]], str]:
    """
    Transcribe audio file using faster-whisper.
    Returns a tuple of (segments_list, detected_language).
    """
    print(f"📦 Loading Whisper AI model '{config.model_size}' into memory... (This might take a moment if downloading for the first time)")
    
    # Suppress ctranslate2 compute type warnings
    if not config.verbose:
        ctranslate2.set_log_level(logging.ERROR)
        
    # Redirect stderr temporarily to completely silence huggingface hub warnings about unauthenticated requests
    original_stderr = sys.stderr
    if not config.verbose:
        sys.stderr = open(os.devnull, 'w')
        
    try:
        # device="auto" defaults to CUDA if available, else CPU.
        # compute_type="default" uses float16 on GPU and int8 on CPU if supported.
        model = WhisperModel(config.model_size, device="auto", compute_type="default")
    finally:
        # Restore stderr
        if not config.verbose:
            sys.stderr.close()
            sys.stderr = original_stderr
    
    print(f"🎙️  Analyzing audio file to detect spoken language...")
    # Generate transcription
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
    
    # Create a progress bar using the total duration of the audio
    total_duration = info.duration
    
    print(f"✍️  Transcribing audio to text...")
    with tqdm(total=total_duration, unit="s", unit_scale=True, bar_format="{l_bar}{bar}| {n_fmt}s/{total_fmt}s audio processed") as pbar:
        for segment in segments:
            result_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            # Update the progress bar based on the end time of the current segment
            pbar.update(segment.end - pbar.n)
            
            if config.verbose:
                tqdm.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
                
        # Ensure progress bar completes
        if pbar.n < total_duration:
            pbar.update(total_duration - pbar.n)
            
    return result_segments, detected_lang
