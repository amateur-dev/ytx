import os
from typing import List, Dict, Any, Tuple
from faster_whisper import WhisperModel
from ytx.config import YtxConfig

def transcribe_audio(audio_path: str, config: YtxConfig) -> Tuple[List[Dict[str, Any]], str]:
    """
    Transcribe audio file using faster-whisper.
    Returns a tuple of (segments_list, detected_language).
    """
    print(f"Loading Whisper model '{config.model_size}'...")
    
    # device="auto" defaults to CUDA if available, else CPU.
    # compute_type="default" uses float16 on GPU and int8 on CPU if supported.
    model = WhisperModel(config.model_size, device="auto", compute_type="default")
    
    print(f"Transcribing {audio_path}...")
    # Generate transcription
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language=config.source_lang,
        condition_on_previous_text=False
    )
    
    detected_lang = info.language
    print(f"Detected language: {detected_lang} (probability: {info.language_probability:.2f})")
    
    result_segments = []
    for segment in segments:
        result_segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
        if config.verbose:
            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            
    return result_segments, detected_lang
