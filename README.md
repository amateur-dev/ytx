```
 __  __  _______  __  __
 \ \/ / |__   __| \ \/ /
  \  /     | |     \  /
  / /      | |     /  \
 /_/       |_|    /_/\_\
```

> **YouTube → Text. Instantly. Locally. Free.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://www.python.org)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-MLX%20GPU-black?style=flat-square&logo=apple)](https://github.com/ml-explore/mlx)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

`ytx` is a local-first command-line tool that turns any YouTube video into a clean, accurate transcript — and translates it into any language using your favourite AI. No cloud account required. No data leaves your machine unless you want it to.

---

## ✨ What makes it special?

| | |
|---|---|
| ⚡ **Blazing fast on Apple Silicon** | Uses `mlx-whisper` to run the full `large-v3` Whisper model on your Mac GPU. A 10-minute video transcribes in under 30 seconds. |
| 🧠 **Best-in-class accuracy** | Locked to `whisper-large-v3` — the highest-quality open-source speech model available. No quality trade-offs. |
| 🌍 **AI Translation** | Pipe results through OpenCode, Claude Code, or any Cloud API (OpenAI / Anthropic / Gemini / OpenRouter) for stunning human-quality translations. |
| 🛑 **Anti-Hallucination** | The AI editor automatically detects and silently removes Whisper's repetitive hallucination loops — pristine output every time. |
| 🎛 **Beautiful interactive wizard** | Run `ytx` for a guided RGB-animated TUI. It remembers your preferences as a preset so future runs are instant. |
| 📦 **Fully local, fully free** | Everything runs on your hardware. No API key needed for transcription. Bring your own key only if you want AI translation. |

---

## 🖥 Requirements

- **Python 3.10+**
- **ffmpeg** (used by yt-dlp internally)

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

---

## 📦 Installation

```bash
git clone https://github.com/your-username/ytx.git
cd ytx
pip install -e .
```

Check your environment is ready:

```bash
ytx doctor
```

> **First run notice:** `ytx` will automatically download the open-source `whisper-large-v3` model from Hugging Face (~3 GB) on first use. You can verify the model at:
> - **Apple Silicon (Mac):** https://huggingface.co/mlx-community/whisper-large-v3-mlx
> - **All other platforms:** https://huggingface.co/Systran/faster-whisper-large-v3

---

## 🤖 Claude Code & AI Agent Skill

Instead of reading this README and running commands manually, you can install the `ytx` Skill for Claude Code (and compatible agents). This teaches your AI agent exactly how to transcribe and translate videos for you automatically.

Install the skill globally so it's available in all your projects:

```bash
mkdir -p ~/.claude/skills/ytx
curl -sL https://raw.githubusercontent.com/your-username/ytx/main/.claude/skills/ytx/SKILL.md -o ~/.claude/skills/ytx/SKILL.md
```

Now, you can just ask Claude from any terminal:
> *"Transcribe this YouTube video: https://youtu.be/VIDEO_ID"*  
> *"Translate this video to Japanese: https://youtu.be/VIDEO_ID"*

---

## 🚀 Quick Start

### Interactive Mode (recommended)

```bash
ytx
```

The wizard guides you through everything — URL, translation, output format — and auto-opens the result folder when done.

### Headless / Scripting Mode

```bash
# Transcribe a video (no translation)
ytx "https://youtu.be/VIDEO_ID"

# Transcribe + translate to Spanish via OpenCode
ytx "https://youtu.be/VIDEO_ID" --to Spanish --translator cli_opencode

# Translate to English using Claude Code
ytx "https://youtu.be/VIDEO_ID" --to English --translator cli_claude_code

# Translate using a Cloud API (requires OPENROUTER_API_KEY / OPENAI_API_KEY etc.)
ytx "https://youtu.be/VIDEO_ID" --to French --translator cloud

# Batch process a list of URLs from a file
ytx --input urls.txt --to English --translator cli_opencode

# Only use official YouTube subtitles (no local transcription)
ytx "https://youtu.be/VIDEO_ID" --official-only

# Output as plain text instead of SRT
ytx "https://youtu.be/VIDEO_ID" --format txt
```

---

## ⚙️ CLI Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--to <language>` | *(none)* | Translate to this language (e.g. `English`, `Spanish`, `Hindi`) |
| `--translator <engine>` | `argos` | Translation engine: `argos` · `cloud` · `cli_opencode` · `cli_claude_code` · `cli_ollama` |
| `--format <fmt>` | `srt` | Output format: `srt` · `vtt` · `txt` · `json` |
| `--output <dir>` | `output/` | Directory to write results into |
| `--official-only` | off | Only download official YouTube subtitles; error if none exist |
| `--allow-auto-subs` | off | Accept YouTube auto-generated captions as fallback |
| `--source-lang <code>` | auto | Force a specific source language (e.g. `hi`, `en`) |
| `--force-transcribe` | off | Skip official subtitles and always run local transcription |
| `--keep-audio` | off | Keep the downloaded audio file after transcription |
| `--input <file>` | *(none)* | Read YouTube URLs from a text file (one per line) |
| `--verbose` | off | Show full debug output |

---

## 🌐 Translation Engines

`ytx` supports multiple translation backends. Pick the one that fits your setup:

### Local AI CLI tools (free, no API key)
These must be installed on your system separately.

| Engine | Flag | Install |
|--------|------|---------|
| [OpenCode](https://opencode.ai) | `cli_opencode` | `npm i -g opencode-ai` |
| [Claude Code](https://claude.ai/code) | `cli_claude_code` | `npm i -g @anthropic-ai/claude-code` |
| [Ollama](https://ollama.com) | `cli_ollama` | [ollama.com](https://ollama.com) |

### Cloud APIs (bring your own key)
Set one of these environment variables (or add to a `.env` file):

```bash
OPENROUTER_API_KEY=...   # Recommended — access 100+ models, has free tier
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
```

Then run with `--translator cloud`.

### Offline fallback
If no AI tool or API key is available, `ytx` falls back to [Argos Translate](https://github.com/argosopentech/argos-translate) — a fully offline neural translation engine. It downloads language packages on first use.

---

## 📁 Output Structure

```
output/
└── Video Title/
    ├── source.info.json               ← video metadata
    ├── source.transcribed.srt         ← raw local transcription
    └── source.translated.English.srt  ← AI-translated output
```

---

## 🔬 How it works

```
YouTube URL
    │
    ▼
yt-dlp fetches metadata
    │
    ├─ Official subtitles exist? ──► Download & done
    │
    └─ No subtitles
         │
         ▼
    Stream m4a audio (no conversion)
         │
         ▼
    whisper-large-v3
    (MLX GPU on Apple Silicon / CPU everywhere else)
         │
         ▼
    Segments with timestamps
         │
         ├─ No translation? ──► Write SRT / VTT / TXT / JSON
         │
         └─ Translation requested
                │
                ▼
           AI engine (CLI / Cloud / Argos)
           + anti-hallucination cleanup
                │
                ▼
           Translated SRT written & folder opened
```

---

## 🤝 Contributing

Pull requests welcome. Please open an issue first for large changes.

```bash
git clone https://github.com/your-username/ytx.git
cd ytx
pip install -e .
ytx doctor  # verify your setup
```

---

## 📄 License

MIT © ytx contributors
