---
name: ytx
description: Transcribes and translates YouTube videos locally using the ytx CLI. Use this when the user asks to transcribe, get subtitles, or translate a YouTube video.
---

# ytx

You have access to the `ytx` command-line tool, a local-first application that turns any YouTube video into a clean, accurate transcript and can translate it into any language. 

When a user asks you to transcribe or translate a YouTube video, use the `run_in_terminal` or equivalent terminal tool to execute `ytx` with the appropriate arguments.

## Common Workflows

### 1. Basic Transcription
If the user just wants the transcript of a video:
```bash
ytx "https://youtu.be/VIDEO_ID"
```

### 2. Transcription + Translation
If the user wants the video translated into another language. Since you are Claude, default to using the `cli_claude_code` translator if asked to translate without specifying an engine:
```bash
ytx "https://youtu.be/VIDEO_ID" --to "Spanish" --translator cli_claude_code
```

### 3. Change Output Format
If the user wants plain text instead of SRT subtitles:
```bash
ytx "https://youtu.be/VIDEO_ID" --format txt
```

### 4. Official Subtitles Only
If the user wants to skip local transcription and just download the official YouTube subtitles:
```bash
ytx "https://youtu.be/VIDEO_ID" --official-only
```

## Flags Reference
- `--to <language>`: Translate to this language (e.g. `English`, `Spanish`).
- `--translator <engine>`: Translation engine (`argos`, `cloud`, `cli_opencode`, `cli_claude_code`, `cli_ollama`).
- `--format <fmt>`: Output format (`srt`, `vtt`, `txt`, `json`). Defaults to `srt`.
- `--output <dir>`: Directory to write results into. Defaults to `output/`.
- `--official-only`: Only download official YouTube subtitles.
- `--force-transcribe`: Skip official subtitles and always run local transcription.
- `--input <file>`: Read YouTube URLs from a text file (one per line).

## Note
By default, the processed files are placed in an `output/` folder in the current directory. When the job completes, read the generated files from that directory if the user asks you questions about the video's content.
