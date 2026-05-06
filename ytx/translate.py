import os
from typing import List, Dict, Any
from ytx.config import YtxConfig

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
    target_lang = config.target_lang
    if not target_lang or source_lang == target_lang:
        return segments
        
    if getattr(config, 'translation_method', 'argos') == "cloud":
        print(f"✨ Cloud AI translation to '{target_lang}' is planned for a future update!")
        print("Falling back to local offline translation for now...")

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
