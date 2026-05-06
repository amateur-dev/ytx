import os
import questionary
from dotenv import load_dotenv, set_key
from typing import Optional, List
from pathlib import Path

from ytx.config import YtxConfig
from ytx.youtube import get_video_info

ENV_FILE_PATH = Path.home() / ".ytx.env"

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

def run_interactive_session(initial_url: Optional[str] = None) -> YtxConfig:
    """Run an interactive Q&A session using questionary to build the config."""
    print("🤖 Welcome to ytx Interactive Mode!\n")
    
    # 1. URL Gathering
    url = initial_url
    if not url:
        url = questionary.text("🔗 What YouTube video do you want to process? (Paste URL):").ask()
        if not url:
            print("\nCancelled.")
            exit(1)

    # 2. Metadata Fetching
    print("🔍 Fetching video details... Please wait.")
    # Create a dummy config just for quiet extraction
    dummy_config = YtxConfig(urls=[url], verbose=False)
    info = get_video_info(url, dummy_config)
    
    if not info:
        print("❌ Could not fetch video info. Exiting.")
        exit(1)
        
    title = info.get('title', 'Unknown Video')
    duration = info.get('duration', 0)
    print(f"\n🎬 Video: \"{title}\" ({duration}s)\n")

    official_subs = info.get('subtitles', {})
    auto_subs = info.get('automatic_captions', {})
    
    config = YtxConfig(urls=[url], interactive=True)
    
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
        
    # Transcription model selection
    if transcribe_action == "transcribe_local":
        model_choices = [
            questionary.Choice("small (Fast & good quality - Recommended)", value="small"),
            questionary.Choice("tiny (Extremely fast, lower quality)", value="tiny"),
            questionary.Choice("base (Fast, okay quality)", value="base"),
            questionary.Choice("medium (Slower, higher quality)", value="medium"),
            questionary.Choice("large-v3 (Slowest, highest quality)", value="large-v3")
        ]
        config.model_size = questionary.select(
            "Which AI model size should I use for transcription?",
            choices=model_choices
        ).ask()
        if not config.model_size:
            exit(1)

    # 4. API Key / Gateway configuration Check
    if not has_cloud_api_key():
        setup_api = questionary.confirm(
            "🔑 I don't see any Cloud API keys configured. Would you like to add one (e.g., OpenRouter) to unlock Cloud AI translation/summaries?",
            default=False
        ).ask()
        
        if setup_api:
            gateway = questionary.select("Which gateway?", choices=["OpenRouter", "OpenAI", "Anthropic", "Gemini"]).ask()
            if gateway:
                key_name = f"{gateway.upper()}_API_KEY"
                key_val = questionary.password(f"Please paste your {gateway} API key:").ask()
                if key_val:
                    save_api_key(key_name, key_val)
                    print(f"✅ Saved to {ENV_FILE_PATH}")

    # 5. Translation options
    translate_choice = questionary.select(
        "Do you want to process the text further?",
        choices=[
            questionary.Choice("No, keep the transcript as-is", value="no"),
            questionary.Choice("Yes, translate using local offline AI (Argos)", value="argos"),
            questionary.Choice("✨ Yes, translate using Cloud AI (Requires API key)", value="cloud", disabled="No API key found" if not has_cloud_api_key() else None)
        ]
    ).ask()
    
    if not translate_choice:
        exit(1)

    if translate_choice != "no":
        target = questionary.text("What is the target language code? (e.g., 'en', 'es', 'fr')").ask()
        if not target:
            exit(1)
        config.target_lang = target
        config.translation_method = translate_choice

    # 6. Format options
    config.output_format = questionary.select(
        "What format do you need?",
        choices=["srt", "txt", "vtt", "json"]
    ).ask()
    
    if not config.output_format:
        exit(1)
    
    print("\n🚀 Configuration complete. Starting pipeline...\n")
    return config
