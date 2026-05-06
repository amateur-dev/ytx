import os
import json
import pycountry
from typing import List, Dict, Any
from ytx.config import YtxConfig
from rich.console import Console

console = Console()

def get_language_code(language_name: str) -> str:
    """Convert a language name like 'Spanish', 'Eng', or 'ES' to a 2-letter language code."""
    language_name = language_name.strip()
    
    if len(language_name) == 2:
        return language_name.lower()
        
    try:
        # lookup() is much smarter than get() - it fuzzy matches "Eng", "English", etc.
        lang = pycountry.languages.lookup(language_name)
        if hasattr(lang, 'alpha_2'):
            return lang.alpha_2
    except Exception:
        pass
        
    return language_name.lower()  # Fallback

def _install_argos_package(from_code: str, to_code: str) -> bool:
    import argostranslate.package
    
    # Update package index
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    
    # Find package
    target_package = None
    for pkg in available_packages:
        if pkg.from_code == from_code and pkg.to_code == to_code:
            target_package = pkg
            break
            
    if target_package:
        print(f"Downloading translation package: {from_code} -> {to_code}...")
        target_package.install()
        return True
    return False

def translate_with_cloud(segments: List[Dict[str, Any]], source_lang: str, target_lang: str) -> List[Dict[str, Any]]:
    """Translate segments using litellm to leverage whatever Cloud API key is available."""
    try:
        import litellm
        
        # Suppress litellm logging noise
        litellm.suppress_debug_info = True
    except ImportError:
        console.print("[bold red]litellm is not installed. Run 'pip install litellm'[/bold red]")
        return None

    # Determine which model to use based on available keys
    model = None
    if os.environ.get("OPENROUTER_API_KEY"):
        model = "openrouter/openai/gpt-4o-mini"
    elif os.environ.get("OPENAI_API_KEY"):
        model = "gpt-4o-mini"
    elif os.environ.get("ANTHROPIC_API_KEY"):
        model = "claude-3-haiku-20240307"
    elif os.environ.get("GEMINI_API_KEY"):
        model = "gemini/gemini-1.5-flash"
    else:
        console.print("[bold red]No valid Cloud API key found in environment.[/bold red]")
        return None

    prompt = (
        f"Translate the following JSON subtitle segments from {source_lang} to {target_lang}.\n"
        f"Maintain the exact JSON structure. Do NOT change the 'start' or 'end' timestamps.\n"
        f"Output ONLY valid JSON. Do not include markdown formatting like ```json.\n\n"
        f"{json.dumps(segments, ensure_ascii=False)}"
    )

    console.print(f"☁️  [cyan]Translating to {target_lang} using Cloud API ({model})...[/cyan]")
    
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": "You are a precise subtitle translator. You only output valid JSON arrays without markdown wrappers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up markdown if the AI disobeyed
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content.strip())
        
    except Exception as e:
        console.print(f"⚠️ [bold red]Cloud API translation failed:[/bold red] {e}")
        return None

def translate_with_cli(segments: List[Dict[str, Any]], source_lang: str, target_lang: str, cli_name: str, cli_command: str) -> List[Dict[str, Any]]:
    """Translate segments by writing them to a temp file and passing instructions to a local AI CLI tool."""
    import tempfile
    import subprocess
    
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
        temp_input = f.name
        
    temp_output = temp_input.replace('.json', '_translated.json')
    
    prompt = (
        f"You are an expert translator. Read the file '{temp_input}'. "
        f"It contains a JSON array of subtitle segments. "
        f"Translate the 'text' field of every segment from {source_lang} to {target_lang}. "
        f"Do NOT change the 'start' or 'end' timestamps. "
        f"Save the completely translated JSON array to a new file named '{temp_output}'. "
        f"Ensure the output is valid JSON. Do not output conversational text."
    )
    
    # Construct the command
    if cli_command == "claude":
        cmd = ["claude", "-p", prompt]
    elif cli_command == "ollama":
        # Assumes llama3 is installed; if not, ollama will pull or fail. 
        # Better to just use a standard prompt model execution.
        cmd = ["ollama", "run", "llama3", prompt] 
    else:
        # Default for opencode, goose, agent, gemini
        cmd = [cli_command, prompt]
        
    console.print(f"🤖 [cyan]Invoking {cli_name} to translate... This may take a moment.[/cyan]")
    
    try:
        # Run the tool and suppress its standard output so it doesn't clutter our terminal
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(temp_output):
            with open(temp_output, 'r') as f:
                translated_segments = json.load(f)
            return translated_segments
        else:
            console.print(f"⚠️ [yellow]{cli_name} failed to create the output file '{temp_output}'.[/yellow]")
    except Exception as e:
        console.print(f"⚠️ [bold red]CLI execution failed:[/bold red] {e}")
    finally:
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)
            
    return None

def translate_segments(segments: List[Dict[str, Any]], source_lang: str, config: YtxConfig) -> List[Dict[str, Any]]:
    """
    Translates a list of transcript segments to the target language.
    Returns the translated segments.
    """
    if not config.target_lang:
        return segments
        
    target_lang = get_language_code(config.target_lang)
    source_lang = get_language_code(source_lang)
    
    if source_lang == target_lang:
        return segments
        
    if getattr(config, 'translation_method', 'argos').startswith("cli_"):
        cli_command = config.translation_method.replace("cli_", "")
        cli_name = cli_command.replace("_", " ").title()
        
        translated = translate_with_cli(segments, source_lang, target_lang, cli_name, cli_command)
        if translated:
            return translated
            
        console.print("[yellow]Falling back to local offline argos translation...[/yellow]")
        
    elif getattr(config, 'translation_method', 'argos') == "cloud":
        translated = translate_with_cloud(segments, source_lang, target_lang)
        if translated:
            return translated
            
        console.print("[yellow]Falling back to local offline argos translation...[/yellow]")

    try:
        import argostranslate.package
        import argostranslate.translate
    except ImportError:
        print("argostranslate module not found. Skipping translation.")
        return segments

    # Check if package is installed
    installed_packages = argostranslate.package.get_installed_packages()
    package_found = False
    for pkg in installed_packages:
        if pkg.from_code == source_lang and pkg.to_code == target_lang:
            package_found = True
            break
            
    if not package_found:
        print(f"Translation package for {source_lang} -> {target_lang} not installed. Attempting to install...")
        success = _install_argos_package(source_lang, target_lang)
        if not success:
            print(f"Failed to find Argos Translate package for {source_lang} -> {target_lang}. Skipping translation.")
            return segments
            
    print(f"Translating {len(segments)} segments from {source_lang} to {target_lang}...")
    translated_segments = []
    for seg in segments:
        text = seg["text"]
        try:
            translated_text = argostranslate.translate.translate(text, source_lang, target_lang)
            translated_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": translated_text
            })
        except Exception as e:
            if config.verbose:
                print(f"Translation error on segment '{text}': {e}")
            # Fallback to original text if translation fails
            translated_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": text
            })
            
    return translated_segments
