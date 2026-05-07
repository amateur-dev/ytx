import os
import yt_dlp
from typing import Dict, Any, Optional
from ytx.config import YtxConfig
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.console import Console

console = Console()

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
    except yt_dlp.utils.DownloadError as e:
        raise RuntimeError(f"yt-dlp blocked or failed: {e.msg}") from e
    except Exception as e:
        if config.verbose:
            console.print(f"[bold red]Exception during metadata extraction: {e}[/bold red]")
        raise RuntimeError(f"Unexpected error during metadata extraction: {e}") from e

def download_audio(url: str, output_path_base: str, config: YtxConfig) -> Optional[str]:
    """Download audio using yt-dlp. We download the lowest bitrate m4a file 
    for blazing fast speed, as Whisper downsamples to 16kHz anyway.
    Returns the path to the downloaded audio file.
    """
    ydl_opts = {
        'format': 'm4a/worstaudio/bestaudio', # Grab the smallest m4a, fallback to worstaudio, then bestaudio
        'quiet': True,
        'no_warnings': True,
        'outtmpl': f"{output_path_base}.%(ext)s",
    }

    if config.verbose:
        ydl_opts['quiet'] = False
        ydl_opts['no_warnings'] = False
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download([url])
                if error_code != 0:
                    raise RuntimeError(f"yt-dlp returned error code {error_code} while downloading audio for {url}")
                
                import glob
                downloaded_files = glob.glob(f"{output_path_base}.*")
                if downloaded_files:
                    return downloaded_files[0]
                raise RuntimeError("Audio download completed but file not found.")
        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(f"yt-dlp blocked or failed: {e.msg}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error during audio download: {e}") from e

    # For non-verbose mode, use a rich progress bar
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
        transient=True
    )
    
    task_id = None
    
    def my_hook(d):
        nonlocal task_id
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if task_id is None:
                task_id = progress.add_task("Downloading audio...", total=total or 100)
            
            if total:
                progress.update(task_id, completed=downloaded, total=total)
            else:
                # Fallback if no total size is known
                progress.update(task_id, completed=downloaded)
        elif d['status'] == 'finished':
            if task_id is not None:
                total = d.get('total_bytes', 100)
                progress.update(task_id, completed=total, total=total)

    ydl_opts['progress_hooks'] = [my_hook]
    
    try:
        with progress:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download([url])
                if error_code != 0:
                    raise RuntimeError(f"yt-dlp returned error code {error_code} while downloading audio for {url}")
                
                # yt-dlp might download an m4a, webm, etc. Let's find out what it saved as
                import glob
                downloaded_files = glob.glob(f"{output_path_base}.*")
                if downloaded_files:
                    return downloaded_files[0]
                raise RuntimeError("Audio download completed but file not found.")
    except yt_dlp.utils.DownloadError as e:
        raise RuntimeError(f"yt-dlp blocked or failed: {e.msg}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error during audio download: {e}") from e
