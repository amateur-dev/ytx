import os
import sys
import platform
import logging
from typing import List, Dict, Any, Tuple
from ytx.config import YtxConfig
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.console import Console
import pycountry

console = Console()

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
        "tiny": "mlx-community/whisper-tiny-mlx",
        "base": "mlx-community/whisper-base-mlx",
        "small": "mlx-community/whisper-small-mlx",
        "medium": "mlx-community/whisper-medium-mlx",
        "large-v3": "mlx-community/whisper-large-v3-mlx"
    }
    repo_id = repo_map.get(config.model_size, "mlx-community/whisper-small-mlx")
    
    console.print(f"⚡ [bold yellow]Using Apple Silicon MLX GPU acceleration![/bold yellow]")
    
    # Pre-download the model so the user sees the progress bar instead of a frozen spinner
    if not config.verbose:
        console.print(f"📦 [dim]Checking/downloading Whisper AI model '{config.model_size}'...[/dim]")
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id=repo_id)
    
    console.print(f"🧠 [dim]Loading model into Mac GPU memory...[/dim]")
    
    decode_options = {
        "condition_on_previous_text": False
    }
    if config.source_lang:
        decode_options["language"] = config.source_lang
        
    original_stderr = sys.stderr
    if not config.verbose:
        sys.stderr = open(os.devnull, 'w')
        
    try:
        # We use a simple spinner here since mlx_whisper.transcribe is currently blocking
        with console.status(f"[cyan]Transcribing audio using Mac GPU... (Incredibly fast!)[/cyan]", spinner="dots"):
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
    console.print(f"✅ [bold green]Detected language:[/bold green] {lang_name}")
    
    result_segments = []
    for segment in result.get("segments", []):
        result_segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip()
        })
        
    console.print(f"✨ [bold green]Transcription complete![/bold green]")
    return result_segments, detected_lang

def transcribe_audio_faster_whisper(audio_path: str, config: YtxConfig) -> Tuple[List[Dict[str, Any]], str]:
    """Transcribe using CPU/CUDA via faster-whisper."""
    
    # Pre-download the model explicitly so the user sees the download progress bar
    if not config.verbose:
        console.print(f"📦 [dim]Checking/downloading Whisper AI model '{config.model_size}'...[/dim]")
    from faster_whisper.utils import download_model as fw_download_model
    fw_download_model(config.model_size)
    
    console.print(f"🧠 [dim]Loading Whisper AI model '{config.model_size}' into memory...[/dim]")
    
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
    
    console.print(f"🎙️  [cyan]Analyzing audio file to detect spoken language...[/cyan]")
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language=config.source_lang,
        condition_on_previous_text=False,
        vad_filter=True, # Explicitly enable Voice Activity Detection
        vad_parameters=dict(min_silence_duration_ms=500) # Skip silences over 500ms
    )
    
    detected_lang = info.language
    lang_name = get_language_name(detected_lang)
    console.print(f"✅ [bold green]Detected language:[/bold green] {lang_name} (Confidence: {info.language_probability:.0%})")
    
    result_segments = []
    total_duration = info.duration
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "•",
        TimeElapsedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("[cyan]Transcribing audio...", total=total_duration)
        
        for segment in segments:
            result_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            progress.update(task, completed=segment.end)
            
            if config.verbose:
                console.print(f"[dim][{segment.start:.2f}s -> {segment.end:.2f}s][/dim] {segment.text}")
                
        # Ensure progress bar completes
        progress.update(task, completed=total_duration)
        
    console.print(f"✨ [bold green]Transcription complete![/bold green]")
    return result_segments, detected_lang

def transcribe_audio(audio_path: str, config: YtxConfig) -> Tuple[List[Dict[str, Any]], str]:
    """Route transcription to the best available backend."""
    if HAS_MLX:
        return transcribe_audio_mlx(audio_path, config)
    else:
        return transcribe_audio_faster_whisper(audio_path, config)
