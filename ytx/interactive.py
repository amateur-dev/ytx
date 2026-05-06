import os
import json
import shutil
import webbrowser
import questionary
from dotenv import load_dotenv, set_key
from typing import Optional, List
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
import time
import math

from ytx.config import YtxConfig
from ytx.youtube import get_video_info
from ytx.transcribe import HAS_MLX

ENV_FILE_PATH = Path.home() / ".ytx.env"
PROFILE_FILE_PATH = Path.home() / ".ytx_profile.json"
console = Console()

def load_env():
    if ENV_FILE_PATH.exists():
        load_dotenv(dotenv_path=ENV_FILE_PATH)

def save_api_key(key_name: str, key_value: str):
    if not ENV_FILE_PATH.exists():
        ENV_FILE_PATH.touch()
    set_key(dotenv_path=ENV_FILE_PATH, key_to_set=key_name, value_to_set=key_value)
    os.environ[key_name] = key_value

def has_cloud_api_key() -> bool:
    load_env()
    return any(os.environ.get(k) for k in [
        "OPENAI_API_KEY", 
        "ANTHROPIC_API_KEY", 
        "GEMINI_API_KEY", 
        "OPENROUTER_API_KEY"
    ])

def detect_local_ai_tools() -> List[str]:
    """Detect installed AI CLI tools on the user's system by checking the PATH."""
    tools = []
    
    # Tool Name -> CLI command to check
    known_clis = {
        "Claude Code": "claude",
        "OpenCode": "opencode",
        "Ollama": "ollama",
        "Gemini CLI": "gemini",
        "Cursor Agent": "agent",
        "Goose": "goose",
        "Aion CLI": "aion"
    }
    
    for name, cmd in known_clis.items():
        if shutil.which(cmd):
            tools.append(name)
            
    return tools

def run_interactive_session(initial_url: Optional[str] = None) -> YtxConfig:
    """Run an interactive Q&A session using questionary to build the config."""
    logo_lines = [
        r" __  __  _______  __  __ ",
        r" \ \/ / |__   __| \ \/ / ",
        r"  \  /     | |     \  /  ",
        r"  / /      | |     /  \  ",
        r" /_/       |_|    /_/\_\ "
    ]
    
    with Live(refresh_per_second=30, console=console) as live:
        revealed = []
        # Smooth reveal down
        for line in logo_lines:
            revealed.append(line)
            current_text = "\n".join(revealed)
            panel = Panel.fit(f"[bold cyan]{current_text}[/bold cyan]", title="[bold yellow]ytx[/bold yellow]", subtitle="[dim]Interactive Mode[/dim]")
            live.update(panel)
            time.sleep(0.15)
            
        # Gamer RGB Gradient Sweep Effect
        full_text = "\n".join(logo_lines)
        
        def get_rgb_hex(step, total_steps):
            # Create a smooth sine wave across RGB channels to simulate an RGB keyboard wave
            r = int((math.sin(step/total_steps * math.pi * 2) * 127) + 128)
            g = int((math.sin(step/total_steps * math.pi * 2 + 2) * 127) + 128)
            b = int((math.sin(step/total_steps * math.pi * 2 + 4) * 127) + 128)
            return f"#{r:02x}{g:02x}{b:02x}"

        steps = 45 # Number of frames in the color sweep
        for i in range(steps):
            color = get_rgb_hex(i, steps)
            panel = Panel.fit(f"[bold {color}]{full_text}[/bold {color}]", title="[bold yellow]ytx[/bold yellow]", subtitle="[dim]Interactive Mode[/dim]")
            live.update(panel)
            time.sleep(0.03) # Smooth 30fps transition
            
        # Settle on the signature crisp cyan
        panel = Panel.fit(f"[bold cyan]{full_text}[/bold cyan]", title="[bold yellow]ytx[/bold yellow]", subtitle="[dim]Interactive Mode[/dim]")
        live.update(panel)
    
    # 1. URL Gathering
    urls = []
    if initial_url:
        urls.append(initial_url)
    else:
        u = questionary.text("🔗 What YouTube video do you want to process? (Paste URL):").ask()
        if not u:
            console.print("\n[bold red]Cancelled.[/bold red]")
            exit(1)
        urls.append(u)

    # 1.5 Load Preset Profile
    config = YtxConfig(urls=urls, interactive=True)
    
    if PROFILE_FILE_PATH.exists():
        try:
            with open(PROFILE_FILE_PATH, 'r') as f:
                profile = json.load(f)
            
            p_trans = profile.get("translation_method", "no")
            p_lang = profile.get("target_lang", "None")
            p_fmt = profile.get("output_format", "srt")
            
            desc = f"Translation: {p_trans} -> {p_lang} | Format: {p_fmt}"
            use_preset = questionary.confirm(f"Found saved preset ({desc}). Use these settings?", default=True).ask()
            
            if use_preset:
                config.translation_method = p_trans
                config.target_lang = p_lang if p_trans != "no" else None
                config.output_format = p_fmt
                config.force_transcribe = True # Presets auto-force transcription for batch speed
                
                print("\n🚀 Using preset configuration. Starting pipeline...\n")
                return config
        except Exception:
            pass # Silently fail on bad profile

    # 2. Metadata Fetching
    console.print(f"\n[dim]🔍 Fetching video details for {len(urls)} video(s)... Please wait.[/dim]")
    # Create a dummy config just for quiet extraction
    dummy_config = YtxConfig(urls=urls, verbose=False)
    
    # We just peek at the first URL to make subtitle decisions if it's a single video
    info = get_video_info(urls[0], dummy_config)
    
    if not info:
        console.print("[bold red]❌ Could not fetch video info. Exiting.[/bold red]")
        exit(1)
        
    title = info.get('title', 'Unknown Video')
    duration = info.get('duration', 0)
    
    if len(urls) == 1:
        console.print(f"\n🎬 [bold green]Video:[/bold green] [white]\"{title}\" ({duration}s)[/white]\n")
    else:
        console.print(f"\n🎬 [bold green]Batch Mode:[/bold green] [white]{len(urls)} videos queued.[/white]\n")

    official_subs = info.get('subtitles', {})
    auto_subs = info.get('automatic_captions', {})
    
    # 3. Subtitle / Transcription Logic
    transcribe_action = "local"
    
    if official_subs:
        lang_list = list(official_subs.keys())
        choices = [
            questionary.Choice(f"📥 Download official subtitles (Found: {', '.join(lang_list[:3])}...)", value="download_official"),
            questionary.Choice("🎙️ Ignore them and transcribe from scratch using local AI", value="transcribe_local")
        ]
        choice = questionary.select(
            "I found official subtitles! What would you like to do?",
            choices=choices
        ).ask()
        
        if not choice:
            exit(1)
            
        if choice == "download_official":
            transcribe_action = "download_official"
            if len(lang_list) == 1:
                config.source_lang = lang_list[0]
            else:
                config.source_lang = questionary.select("Which language?", choices=lang_list).ask()
                if not config.source_lang:
                    exit(1)
        else:
            config.force_transcribe = True
                
    elif auto_subs:
        choices = [
            questionary.Choice("🎙️ Transcribe using high-quality local AI (Recommended)", value="transcribe_local"),
            questionary.Choice("📥 Just download the YouTube auto-generated captions", value="download_auto")
        ]
        choice = questionary.select(
            "This video only has YouTube's auto-generated captions. What would you like to do?",
            choices=choices
        ).ask()
        
        if not choice:
            exit(1)
            
        if choice == "download_auto":
            transcribe_action = "download_auto"
            config.allow_auto_subs = True
            lang_list = list(auto_subs.keys())
            if len(lang_list) == 1:
                config.source_lang = lang_list[0]
            else:
                config.source_lang = questionary.select("Which language?", choices=lang_list).ask()
                if not config.source_lang:
                    exit(1)
        else:
            config.force_transcribe = True
                
    else:
        print("ℹ️ No subtitles exist for this video. I will extract the audio and transcribe it.")

    # We now strictly use the large-v3 model. Add the first-time caution message.
    if transcribe_action == "transcribe_local":
        console.print("\n[bold yellow]Notice:[/bold yellow] [white]YTX ensures maximum quality by exclusively using the state-of-the-art [bold cyan]large-v3[/bold cyan] AI model.[/white]")
        console.print("[dim]If this is your first time using YTX, it will download the open-source model (~3GB) from Hugging Face:[/dim]")
        if HAS_MLX:
            console.print("[dim]Link: https://huggingface.co/mlx-community/whisper-large-v3-mlx[/dim]\n")
        else:
            console.print("[dim]Link: https://huggingface.co/Systran/faster-whisper-large-v3[/dim]\n")

    # 4. API Key / Gateway / Local CLI configuration Check
    local_tools = detect_local_ai_tools()
    
    if not has_cloud_api_key():
        if not local_tools:
            prompt_msg = "🔑 I see that you do not have Claude Code, OpenCode, Ollama, or Gemini CLI installed.\n   Do you have an API Key that I could use? (I can help you configure an OpenRouter Free API key instantly!)"
            setup_api = questionary.confirm(prompt_msg, default=False).ask()
            
            if setup_api:
                gateway = questionary.select("Which gateway?", choices=["OpenRouter", "OpenAI", "Anthropic", "Gemini"]).ask()
                if gateway:
                    if gateway == "OpenRouter":
                        print("🌐 Opening browser to generate your OpenRouter key...")
                        try:
                            webbrowser.open("https://openrouter.ai/keys")
                        except Exception:
                            print("💡 Tip: You can get a free API key instantly at https://openrouter.ai/keys")
                    
                    key_name = f"{gateway.upper()}_API_KEY"
                    key_val = questionary.password(f"Please paste your {gateway} API key:").ask()
                    
                    if key_val:
                        # Basic validation - OpenRouter keys typically start with sk-or-v1-
                        if gateway == "OpenRouter" and not key_val.startswith("sk-or-v1-"):
                            print("⚠️ Warning: This doesn't look like a standard OpenRouter key, but I'll save it anyway.")
                            
                        save_api_key(key_name, key_val)
                        print(f"✅ Saved {gateway} API Key to {ENV_FILE_PATH}")
        else:
            tools_str = ", ".join(local_tools)
            print(f"✨ Detected installed AI tools: {tools_str}. I can use them to power advanced AI features!")

    # 5. Translation options
    has_keys = has_cloud_api_key()
    
    translation_choices = [
        questionary.Choice("🛑 No, keep the raw transcript as-is", value="no"),
        questionary.Choice("Yes, translate using local offline AI (Argos - basic quality)", value="argos"),
    ]
    
    for tool in local_tools:
        translation_choices.append(
            questionary.Choice(f"✨ Yes, clean up and/or translate using your installed {tool}", value=f"cli_{tool.lower().replace(' ', '_')}")
        )
        
    translation_choices.append(
        questionary.Choice("✨ Yes, clean up and/or translate using Cloud API", value="cloud", disabled="No API key configured" if not has_keys else None)
    )

    translate_choice = questionary.select(
        "Do you want to process/translate the transcript with AI?",
        choices=translation_choices
    ).ask()
    
    if not translate_choice:
        exit(1)

    if translate_choice != "no":
        target = questionary.autocomplete(
            "What is the target language? (Arrow keys to select or type to search) [Default: English]",
            choices=["English", "Spanish", "French", "German", "Italian", "Portuguese", "Hindi", "Japanese", "Korean", "Chinese"],
            default="English",
            ignore_case=True
        ).ask()
        
        if not target:
            target = "English" # Default to English if they just press Enter or clear it
            
        config.target_lang = target
        config.translation_method = translate_choice

    # 6. Format options
    config.output_format = questionary.select(
        "What format do you need?",
        choices=[
            questionary.Choice("SRT (Recommended for video players/YouTube)", value="srt"),
            questionary.Choice("TXT (Plain text for reading)", value="txt"),
            questionary.Choice("VTT (For web video players)", value="vtt"),
            questionary.Choice("JSON (For developers/API)", value="json")
        ]
    ).ask()
    
    if not config.output_format:
        exit(1)
        
    # Save Preset
    try:
        save_preset = questionary.confirm("Would you like to save these settings as your default preset?", default=True).ask()
        if save_preset:
            with open(PROFILE_FILE_PATH, 'w') as f:
                json.dump({
                    "translation_method": getattr(config, 'translation_method', 'no'),
                    "target_lang": getattr(config, 'target_lang', 'None'),
                    "output_format": config.output_format
                }, f)
    except Exception:
        pass
    
    print("\n🚀 Configuration complete. Starting pipeline...\n")
    return config
