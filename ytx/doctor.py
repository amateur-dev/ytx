import shutil
import sys
import importlib

def check_command(cmd_name: str) -> bool:
    """Check if a system command is available."""
    path = shutil.which(cmd_name)
    if path:
        print(f"✅ {cmd_name} found at: {path}")
        return True
    else:
        print(f"❌ {cmd_name} NOT found in PATH.")
        return False

def check_module(module_name: str) -> bool:
    """Check if a python module is available."""
    try:
        importlib.import_module(module_name)
        print(f"✅ Python module '{module_name}' is installed.")
        return True
    except ImportError:
        print(f"❌ Python module '{module_name}' is missing.")
        return False

def run_doctor() -> int:
    """Run environment checks."""
    print("Running environment checks...")
    print("-" * 30)
    
    success = True
    
    # Check binaries
    if not check_command("ffmpeg"):
        success = False
        print("   -> Please install ffmpeg (e.g. `brew install ffmpeg` on macOS).")
    
    if not check_command("yt-dlp"):
        success = False
        print("   -> Please install yt-dlp (e.g. `brew install yt-dlp` or via pip).")

    # Check python dependencies
    if not check_module("yt_dlp"):
        success = False
    if not check_module("faster_whisper"):
        success = False
    if not check_module("argostranslate"):
        success = False
        
    print("-" * 30)
    if success:
        print("All dependencies are satisfied. You are ready to go!")
        return 0
    else:
        print("Some dependencies are missing. Please fix them and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(run_doctor())
