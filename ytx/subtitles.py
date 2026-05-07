import os
import yt_dlp
from typing import Dict, Any, Optional, Tuple
from ytx.config import YtxConfig

def has_usable_subtitles(info: Dict[str, Any], config: YtxConfig) -> Tuple[bool, Optional[str], bool]:
    """
    Checks if there are usable subtitles based on the config.
    Returns (has_subs, lang_code, is_auto)
    """
    subs = info.get('subtitles', {})
    auto_subs = info.get('automatic_captions', {})
    
    preferred_lang = config.source_lang

    # 1. Check official subtitles
    if preferred_lang:
        if preferred_lang in subs:
            return True, preferred_lang, False
    else:
        # If no preferred lang, pick 'en' first or the first available
        if 'en' in subs:
            return True, 'en', False
        elif subs:
            return True, list(subs.keys())[0], False

    # 2. Check auto-generated subtitles if allowed
    if config.allow_auto_subs:
        if preferred_lang:
            if preferred_lang in auto_subs:
                return True, preferred_lang, True
        else:
            if 'en' in auto_subs:
                return True, 'en', True
            elif auto_subs:
                return True, list(auto_subs.keys())[0], True
                
    return False, None, False

def download_subtitles(url: str, lang: str, is_auto: bool, output_path_base: str, config: YtxConfig) -> Optional[str]:
    """
    Downloads subtitles using yt-dlp.
    Returns the path to the downloaded subtitle file.
    """
    # yt-dlp tends to add the language code to the file name, e.g., output.en.srt
    ydl_opts = {
        'quiet': not config.verbose,
        'no_warnings': not config.verbose,
        'skip_download': True,
        'writesubtitles': not is_auto,
        'writeautomaticsub': is_auto,
        'subtitleslangs': [lang],
        'subtitlesformat': config.output_format if config.output_format in ['srt', 'vtt'] else 'best',
        'outtmpl': f"{output_path_base}",
    }
    
    # For outtmpl yt-dlp appends .LANG.ext for subtitles.
    # We will need to find the file afterwards.
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            error_code = ydl.download([url])
            if error_code != 0:
                raise RuntimeError(f"yt-dlp returned error code {error_code} while downloading subtitles for {url}")
            
            # Find the downloaded file
            ext = config.output_format if config.output_format in ['srt', 'vtt'] else 'vtt'
            expected_file = f"{output_path_base}.{lang}.{ext}"
            
            # Sometimes yt-dlp converts vtt to srt or saves as vtt if srt is not available without ffmpeg conversion
            # So we check around.
            dir_name = os.path.dirname(output_path_base) or "."
            base_name = os.path.basename(output_path_base)
            
            for file in os.listdir(dir_name):
                if file.startswith(base_name) and (file.endswith(f".{lang}.vtt") or file.endswith(f".{lang}.srt")):
                    return os.path.join(dir_name, file)
                    
            if os.path.exists(expected_file):
                return expected_file
            else:
                raise RuntimeError("Subtitle download completed but file not found.")
            
    except yt_dlp.utils.DownloadError as e:
        raise RuntimeError(f"yt-dlp blocked or failed to download subtitles: {e.msg}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error during subtitle download: {e}") from e
