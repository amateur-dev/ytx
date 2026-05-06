# ytx

`ytx` is a smart, local-first command-line tool for extracting YouTube transcripts. It features a beautiful interactive terminal wizard, prioritizes official subtitles, falls back to local audio transcription using `faster-whisper`, and offers both offline and cloud-based translation.

## ✨ Features
- **Interactive UI:** Don't want to memorize CLI flags? Just type `ytx` and let the interactive wizard guide you through the process.
- **Smart Fallback:** Prefers official YouTube subtitles (avoiding auto-generated ones by default).
- **Local Transcription:** If no official subtitles exist, it downloads the audio and transcribes it locally on your machine using [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
- **AI CLI Auto-Detection:** Automatically detects installed AI CLI tools on your system (like Claude Code, OpenCode, Cursor, Goose, Ollama, Gemini) to power advanced translation and summarization workflows.
- **Offline & Cloud Translation:** Translates transcripts using local offline models ([Argos Translate](https://github.com/argosopentech/argos-translate)) or helps you instantly configure Cloud APIs (OpenRouter, OpenAI, Anthropic) securely to `~/.ytx.env`.
- **Headless Automation:** fully supports traditional CLI flags for use in scripts and cron jobs.

## 🛠 Requirements
- Python 3.10+
- `ffmpeg` (required for reliable audio extraction)

### macOS System Dependencies
```bash
brew install ffmpeg yt-dlp
```

## 📦 Installation
Clone this repository and install it via pip:
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
Simply type `ytx` to launch the interactive wizard. You can also pass a URL directly to skip the first question:
```bash
ytx
# OR
ytx "https://youtube.com/watch?v=VIDEO_ID"
```
The wizard will intelligently probe the video and offer you context-aware choices (e.g., downloading official subtitles if they exist, or offering to transcribe it from scratch).

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
| `--model <size>` | Select the `faster-whisper` model size (`tiny`, `base`, `small`, `medium`, `large-v3`). Default is `small`. |
| `--output <dir>` | Choose output directory. Default is `output/`. |
| `--keep-audio` | Keep the downloaded audio file after transcription. |
| `--input <file>` | Read URLs from a text file for batch processing. |
| `--verbose` | Show full internal tool output for debugging. |

## 📁 Output Structure
By default, `ytx` creates an `output` directory and groups files by the video's title:
```text
output/
  Video_Title/
    source.info.json
    source.original.en.srt       # If official subtitles were found
    source.transcribed.srt       # If local transcription was used
    source.translated.es.srt     # If translation was requested
```
