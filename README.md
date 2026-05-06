# ytx

`ytx` is a blazing fast, smart command-line tool for extracting, transcribing, cleaning, and translating YouTube subtitles. It features a beautiful RGB animated interactive terminal wizard, prioritizes official subtitles, and falls back to ultra-optimized local audio transcription using Apple Silicon MLX GPU acceleration.

## ✨ Features
- **Interactive UI & Smart Presets:** Type `ytx` for a beautiful interactive wizard. It remembers your favorite settings (Model, Format, AI Engine) so you can process future videos instantly!
- **Apple Silicon GPU Acceleration:** Automatically detects M-series Macs and routes processing through `mlx-whisper` using greedy decoding, slashing transcription time from minutes to seconds.
- **Lightning Audio Extraction:** Directly streams YouTube's lowest-bitrate m4a files straight into Whisper, bypassing slow ffmpeg WAV conversions entirely.
- **Multi-Video Queue:** Paste multiple YouTube URLs back-to-back to process entire playlists or batches of videos unattended.
- **Universal AI Translation & Clean-Up:** Connects to Cloud APIs (OpenAI, Anthropic, Gemini, OpenRouter) or your favorite local AI CLI tools (OpenCode, Claude Code, Goose, Agent, Ollama). 
  - *Anti-Hallucination:* The AI doesn't just translate; it acts as an intelligent editor, silently removing repetitive Whisper hallucinations (e.g., background noise loops) for pristine transcripts.
- **Smart Fallback:** Prefers official YouTube subtitles (avoiding auto-generated ones by default).
- **Auto-Open Output:** On macOS, perfectly drops you straight into the Finder folder the second processing is complete!

## 🛠 Requirements
- Python 3.10+
- `ffmpeg` (required for yt-dlp fallback)

### macOS System Dependencies
```bash
brew install ffmpeg yt-dlp
```

## 📦 Installation
Clone this repository and install it via pip in editable mode:
```bash
git clone <your-repo-url>
cd ytx
pip install -e .
```

You can verify your environment and dependencies at any time by running:
```bash
ytx doctor
```

## 🚀 Usage

### Interactive Mode (Recommended)
Simply type `ytx` to launch the interactive wizard. 
```bash
ytx
```
*Tip: You can queue multiple videos during the URL prompt. Hit Enter on a blank line to start processing!*

### Headless / Automation Mode
If you provide any specific formatting or language flags, `ytx` automatically bypasses the interactive wizard and runs headlessly:

**1. Strictly download official subtitles only (fail if none exist):**
```bash
ytx "https://youtube.com/watch?v=VIDEO_ID" --official-only
```

**2. Transcribe and translate to Spanish (`es`):**
```bash
ytx "https://youtube.com/watch?v=VIDEO_ID" --to es
```

**3. Batch process multiple URLs from a file and output as plain text:**
```bash
ytx --input urls.txt --format txt
```

## ⚙️ CLI Options
| Option | Description |
|--------|-------------|
| `--official-only` | Download only official subtitles; error if absent. |
| `--allow-auto-subs` | Permit YouTube auto-generated subtitles as a fallback before transcription. |
| `--source-lang <code>` | Prefer a specific source language code; otherwise auto-detect during transcription. |
| `--to <code>` | Translate transcript to the target language code (e.g., `en`, `es`, `fr`). |
| `--format <format>` | Choose output format: `srt` (default), `vtt`, `txt`, or `json`. |
| `--model <size>` | Select the Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`). Default is `small`. |
| `--output <dir>` | Choose output directory. Default is `output/`. |
| `--keep-audio` | Keep the downloaded audio file after transcription. |
| `--input <file>` | Read URLs from a text file for batch processing. |
| `--verbose` | Show full internal tool output and download progress bars for debugging. |

## 📁 Output Structure
By default, `ytx` creates an `output` directory and groups files by the video's title:
```text
output/
  Video_Title/
    source.info.json
    source.original.en.srt       # If official subtitles were found
    source.transcribed.srt       # If local transcription was used
    source.translated.es.srt     # If translation/clean-up was requested
```
