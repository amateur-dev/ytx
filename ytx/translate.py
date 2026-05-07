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
    """Translate or clean segments using litellm to leverage whatever Cloud API key is available."""
    try:
        import litellm
        
        # Suppress litellm logging noise
        litellm.suppress_debug_info = True
    except ImportError as e:
        raise RuntimeError("Cloud translation requires 'litellm'. Run 'pip install litellm'.") from e

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
        raise RuntimeError("No valid Cloud API key found in environment (OPENROUTER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY).")

    is_same_lang = (source_lang == target_lang)
    
    if is_same_lang:
        system_role = "You are an expert transcript editor. You only output valid JSON arrays without markdown wrappers."
        task_instruction = (
            f"Clean up and format the following JSON subtitle segments in {source_lang}.\n"
            f"Fix grammar/spelling and SILENTLY REMOVE repetitive hallucinations (e.g., repeating nonsense, repeated syllables) caused by background noise. Leave the text string empty if the whole segment is a hallucination.\n"
            f"Do NOT translate it to another language."
        )
        action_msg = f"🧹 [cyan]Running AI clean-up pass on {source_lang} transcript ({model})...[/cyan]"
    else:
        system_role = "You are a precise subtitle translator and editor. You only output valid JSON arrays without markdown wrappers."
        task_instruction = (
            f"Translate the following JSON subtitle segments from {source_lang} to {target_lang}.\n"
            f"IMPORTANT: While translating, also act as a strict clean-up editor. If you see repetitive hallucinations "
            f"(e.g., repeating the same word infinitely, repeated syllables, or blocks of text where the exact same words repeat for 10+ seconds) caused by background noise, SILENTLY REMOVE the gibberish. Leave the text string empty if the whole segment is a hallucination."
        )
        action_msg = f"☁️  [cyan]Translating to {target_lang} using Cloud API ({model})...[/cyan]"

    prompt = (
        f"{task_instruction}\n"
        f"Maintain the exact JSON structure. Do NOT change the 'start' or 'end' timestamps.\n"
        f"Output ONLY valid JSON. Do not include markdown formatting like ```json.\n\n"
        f"{json.dumps(segments, ensure_ascii=False)}"
    )

    console.print(action_msg)
    
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_role},
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
            
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Cloud API returned invalid JSON: {e}\nRaw output preview: {content[:200]}...") from e
        
    except Exception as e:
        raise RuntimeError(f"Cloud API translation failed: {e}") from e

def translate_with_cli(segments: List[Dict[str, Any]], source_lang: str, target_lang: str, cli_name: str, cli_command: str) -> List[Dict[str, Any]]:
    """Translate or clean segments by embedding them inline in the prompt for a local AI CLI tool."""
    import subprocess
    import shutil

    if not shutil.which(cli_command.split()[0]):
        raise RuntimeError(f"Translation failed: The command '{cli_command.split()[0]}' is not found in your PATH. Please install {cli_name}.")

    segments_json = json.dumps(segments, ensure_ascii=False)
    is_same_lang = (source_lang == target_lang)

    if is_same_lang:
        task_instruction = (
            f"You are an expert transcript editor. Below is a JSON array of subtitle segments in {source_lang}.\n"
            f"TASK: Clean up the 'text' field of every segment. Fix spelling/grammar mistakes and SILENTLY REMOVE "
            f"repetitive hallucinations (e.g., endless repeating nonsense, repeated syllables, or blocks where the same words repeat for 10+ seconds) caused by background noise. "
            f"Leave the text string empty if the whole segment is a hallucination. "
            f"DO NOT translate to another language. Keep it in {source_lang}.\n"
        )
        action_msg = f"🤖 [cyan]Invoking {cli_name} for AI clean-up pass... This may take a moment.[/cyan]"
    else:
        task_instruction = (
            f"You are an expert subtitle translator. Below is a JSON array of subtitle segments.\n"
            f"TASK: Translate the 'text' field of every segment from {source_lang} to {target_lang}. "
            f"While translating, also silently remove any repetitive hallucinations "
            f"(e.g., repeated words/syllables for 10+ seconds) — leave 'text' empty for fully hallucinated segments.\n"
        )
        action_msg = f"🤖 [cyan]Invoking {cli_name} to translate to {target_lang}... This may take a moment.[/cyan]"

    prompt = (
        f"{task_instruction}"
        f"RULES:\n"
        f"- Do NOT change 'start' or 'end' timestamp values.\n"
        f"- Output ONLY the raw JSON array. No markdown fences, no explanation, no extra text.\n\n"
        f"INPUT JSON:\n{segments_json}"
    )

    # Construct the command — embed prompt as inline argument
    if cli_command in ("claude", "claude_code"):
        cmd = ["claude", "-p", prompt]
    elif cli_command == "opencode":
        cmd = ["opencode", "run", prompt]
    elif cli_command == "ollama":
        cmd = ["ollama", "run", "llama3", prompt]
    else:
        cmd = [cli_command, prompt]

    console.print(action_msg)

    result = None
    try:
        import threading
        import time as _time
        from rich.live import Live
        from rich.text import Text

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        start = _time.monotonic()
        with Live(console=console, refresh_per_second=4) as live:
            while proc.poll() is None:
                elapsed = int(_time.monotonic() - start)
                mins, secs = divmod(elapsed, 60)
                live.update(Text(f"⏳ {cli_name} thinking... {mins}m {secs:02d}s elapsed", style="cyan"))
                _time.sleep(0.25)

        stdout, stderr = proc.communicate()
        result = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)

        if result.returncode != 0:
            raise RuntimeError(f"{cli_name} exited with error code {result.returncode}.\nStderr: {result.stderr[:500]}")

        content = result.stdout.strip()

        if not content:
            raise RuntimeError(f"{cli_name} returned empty output. Stderr: {result.stderr[:300]}")

        # Strip markdown code fences if the model disobeyed
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        # Extract JSON array even if surrounded by conversational text
        start_idx = content.find("[")
        end_idx = content.rfind("]")
        if start_idx != -1 and end_idx != -1:
            content = content[start_idx:end_idx + 1]

        return json.loads(content.strip())

    except json.JSONDecodeError as e:
        raw_output = result.stdout[:500] if result else "None"
        raise RuntimeError(f"Failed to parse {cli_name} output as JSON: {e}\nRaw output: {raw_output}") from e
    except Exception as e:
        raise RuntimeError(f"CLI execution failed for {cli_name}: {e}") from e

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
        # If using argos, it cannot do monolingual cleanup, so skip it
        if getattr(config, 'translation_method', 'argos') == "argos":
            return segments
        
    if getattr(config, 'translation_method', 'argos').startswith("cli_"):
        cli_command = config.translation_method.replace("cli_", "")
        cli_name = cli_command.replace("_", " ").title()
        
        translated = translate_with_cli(segments, source_lang, target_lang, cli_name, cli_command)
        if translated:
            return translated

        # Same-language: argos has no monolingual package — just return originals
        if source_lang == target_lang:
            console.print("[yellow]CLI failed; no fallback for same-language cleanup. Using original transcript.[/yellow]")
            return segments

        console.print("[yellow]Falling back to local offline argos translation...[/yellow]")

    elif getattr(config, 'translation_method', 'argos') == "cloud":
        translated = translate_with_cloud(segments, source_lang, target_lang)
        if translated:
            return translated

        if source_lang == target_lang:
            console.print("[yellow]Cloud failed; no fallback for same-language cleanup. Using original transcript.[/yellow]")
            return segments

        console.print("[yellow]Falling back to local offline argos translation...[/yellow]")

    try:
        import argostranslate.package
        import argostranslate.translate
    except ImportError as e:
        raise RuntimeError("argostranslate module not found. Run 'pip install argostranslate' or check your environment.") from e

    # Check if package is installed
    installed_packages = argostranslate.package.get_installed_packages()
    package_found = False
    for pkg in installed_packages:
        if pkg.from_code == source_lang and pkg.to_code == target_lang:
            package_found = True
            break
            
    if not package_found:
        print(f"Translation package for {source_lang} -> {target_lang} not installed. Attempting to install...")
        try:
            success = _install_argos_package(source_lang, target_lang)
            if not success:
                raise RuntimeError(f"Failed to find Argos Translate package for {source_lang} -> {target_lang}.")
        except Exception as e:
            raise RuntimeError(f"Error while installing Argos package: {e}") from e
            
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
            raise RuntimeError(f"Argos translation failed for segment '{text}': {e}") from e
            if config.verbose:
                print(f"Translation error on segment '{text}': {e}")
            # Fallback to original text if translation fails
            translated_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": text
            })
            
    return translated_segments
