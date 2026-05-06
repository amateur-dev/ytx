import os
import pycountry
from typing import List, Dict, Any
from ytx.config import YtxConfig

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
        cli_name = config.translation_method.replace("cli_", "").replace("_", " ").title()
        print(f"✨ Routing translation to local {cli_name} CLI is planned for a future update!")
        print("Falling back to local offline argos translation for now...")
    elif getattr(config, 'translation_method', 'argos') == "cloud":
        print(f"✨ Cloud AI translation to '{target_lang}' is planned for a future update!")
        print("Falling back to local offline argos translation for now...")

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
