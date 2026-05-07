# ytx

> **Fast, local transcripts and translations for YouTube videos.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://www.python.org)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-MLX%20GPU-black?style=flat-square&logo=apple)](https://github.com/ml-explore/mlx)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

`ytx` is a local-first command-line tool designed for creators, editors, researchers, and archivists. It turns YouTube videos you are authorized to process into clean, highly accurate transcripts and translates them into multiple languages using on-device AI. 

No cloud transcription accounts required. No data leaves your machine unless you explicitly connect a translation API.

👉 **[View the Live Demo & RGB Landing Page](https://amateur-dev.github.io/ytx/)** 🎬

---

## ✨ Features

| | |
|---|---|
| ⚡ **Blazing Fast on Apple Silicon** | Uses `mlx-whisper` to run the full `large-v3` Whisper model on your Mac GPU. Process a 10-minute video locally in under 30 seconds. |
| 🧠 **Studio-Grade Accuracy** | Locked to `whisper-large-v3` — delivering pristine, open-source speech recognition for researchers and creators. |
| 🌍 **Universal Translation** | Pipe transcripts through local agents (Claude Code, OpenCode) or Cloud APIs (OpenAI / Anthropic) to localize your content. |
| 🛡️ **Anti-Hallucination Editor** | Automatically detects and silently removes Whisper's repetitive audio hallucinations caused by background noise. |
| 🎛 **Interactive Wizard** | Run `ytx` for a guided TUI that remembers your preferences, making repetitive workflows effortless. |
| 🔒 **Privacy-First Processing** | Everything runs on your hardware. Bring your own API key only if you require cloud translation. |

---

## 🎯 Why this exists

Content workflows demand speed, accuracy, and privacy. Existing transcription services often require uploading massive files to the cloud, paying per-minute fees, or dealing with vendor lock-in. 

`ytx` was built to leverage the incredible power of modern local hardware (like Apple Silicon) and the Whisper model, putting high-fidelity transcription and localization directly in the terminal for the content you manage.

---

## 🖥 Requirements

- **Python 3.10+**
- **ffmpeg** (used internally for audio stream processing)

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

---

## 📦 Installation

Install `ytx` directly from GitHub:

```bash
pip install git+https://github.com/amateur-dev/ytx.git
```

Check your environment is ready:

```bash
ytx doctor
```

> **First-run notice:** `ytx` automatically downloads the open-source `whisper-large-v3` model from Hugging Face (~3 GB) on its first execution.

---

## 🚀 Quick Start

There are three main ways to use `ytx` based on your workflow:

### Mode 1: Claude Code & AI Agent Skill (Recommended)

Instead of manually crafting commands, you can install the `ytx` Skill for Claude Code (and compatible AI agents). This teaches your agent how to transcribe and translate videos autonomously.

Install the skill globally so it's available in all your projects:

```bash
mkdir -p ~/.claude/skills/ytx
curl -sL https://raw.githubusercontent.com/amateur-dev/ytx/main/.claude/skills/ytx/SKILL.md -o ~/.claude/skills/ytx/SKILL.md
```

Now, just launch `claude` and ask it:
> *"Transcribe this YouTube video: https://youtu.be/VIDEO_ID"*  
> *"Translate this video to Japanese: https://youtu.be/VIDEO_ID"*

### Mode 2: Interactive Wizard

If you prefer a guided UI, simply run the command with no arguments:

```bash
ytx
```

The terminal wizard will guide you through URL input, translation choices, and output formats.

### Mode 3: Headless / Scripting Mode

If you are writing bash scripts or know exactly what you want:

```bash
# Transcribe your own uploaded video (no translation)
ytx "https://youtu.be/VIDEO_ID"

# Translate a talk/interview you have rights to process to Spanish using Claude CLI
ytx "https://youtu.be/VIDEO_ID" --to Spanish --translator cli_claude_code

# Translate using a Cloud API (requires OPENROUTER_API_KEY / OPENAI_API_KEY etc.)
ytx "https://youtu.be/VIDEO_ID" --to French --translator cloud

# Generate subtitles for editing/accessibility by pulling existing official subtitles
ytx "https://youtu.be/VIDEO_ID" --official-only

# Output as plain text instead of SRT
ytx "https://youtu.be/VIDEO_ID" --format txt
```

---

## ⚙️ CLI Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--to <language>` | *(none)* | Translate to this language (e.g. `English`, `Spanish`) |
| `--translator <engine>` | `argos` | Translation engine: `argos` · `cloud` · `cli_opencode` · `cli_claude_code` · `cli_ollama` |
| `--format <fmt>` | `srt` | Output format: `srt` · `vtt` · `txt` · `json` |
| `--output <dir>` | `output/` | Directory to write results into |
| `--official-only` | off | Only download official subtitles; error if none exist |
| `--allow-auto-subs` | off | Accept auto-generated captions as fallback |
| `--source-lang <code>` | auto | Force a specific source language (e.g. `hi`, `en`) |
| `--force-transcribe` | off | Skip official subtitles and always run local transcription |
| `--keep-audio` | off | Keep the processed audio file after transcription |
| `--input <file>` | *(none)* | Read URLs from a text file for batch processing |

---

## 🌐 Translation Engines

`ytx` supports multiple translation backends to suit your privacy and workflow needs:

### Local AI CLI tools (Free)
These must be installed on your system separately.
- `cli_opencode`
- `cli_claude_code`
- `cli_ollama`

### Cloud APIs (Bring your own key)
Set one of these environment variables (or add to a `.env` file), then run with `--translator cloud`:
- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`

### Offline Fallback
If no AI tool or API key is available, `ytx` defaults to Argos Translate — a fully offline neural translation engine.

---

## 📁 Output Structure

Processed files are saved in an organized, human-readable directory:

```
output/
└── Video_Title/
    ├── source.info.json               ← video metadata
    ├── source.transcribed.srt         ← raw local transcription
    └── source.translated.English.srt  ← AI-translated output
```

---

## Compliance and permitted use

`ytx` is a workflow tool designed for content creators, researchers, editors, and archivists to process videos they are legally authorized to interact with.

Users of `ytx` are responsible for ensuring they have the appropriate rights, licenses, or authorizations to transcribe, translate, and process the media they input. Do not use this tool to process, redistribute, or reproduce copyrighted material without permission from the rights holder. Ensure your use complies with the Terms of Service of the platforms you access. The project does not grant rights to third-party content.

## Trademark notice

"YouTube" is a trademark of Google LLC. `ytx` is an independent open-source project and is not affiliated with, endorsed by, or sponsored by Google LLC or YouTube in any way.

---

## 📄 License

MIT © amateur-dev
