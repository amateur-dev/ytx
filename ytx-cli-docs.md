# ytx CLI — Product and Technical Spec

## Overview

`ytx` is a local-first command-line tool for turning a YouTube URL into a transcript file, with a strict fallback order: prefer official subtitles, otherwise download audio and transcribe locally, then optionally translate the transcript into a target language.[cite:25][cite:68][cite:64]

The tool is designed for macOS first, but the architecture should remain portable to Linux and Windows because its core dependencies are `yt-dlp`, `faster-whisper`, and Argos Translate.[cite:16][cite:68][cite:64]

## Goals

- Accept one or more YouTube URLs as input.[cite:8]
- Prefer **official** subtitles and avoid auto-generated subtitles unless the user explicitly enables them.[cite:25][cite:30]
- If official subtitles are unavailable, download audio only and transcribe it locally in the source language using `faster-whisper`.[cite:68][cite:65]
- If translation is requested, translate the completed transcript into a user-selected target language using an open-source translation engine.[cite:64][cite:66]
- Work as a single user-facing CLI command even if multiple internal steps are required.[cite:25][cite:68]

## Non-goals

- The first version should not try to be a GUI app.[cite:68]
- The first version should not promise perfect “meaning-level” translation quality offline, because offline open-source translation quality varies by language pair and model availability.[cite:64][cite:66]
- The first version should not depend on cloud APIs for core functionality.[cite:64][cite:68]

## Core behavior

The CLI should follow this decision tree for each input URL:[cite:25][cite:68]

1. Inspect the video metadata and available subtitle tracks with `yt-dlp`.[cite:8][cite:25]
2. If official subtitles exist in the preferred source language, download them and stop unless the user asks for translation.[cite:25][cite:30]
3. If official subtitles do not exist, download audio only with `yt-dlp`.[cite:8][cite:68]
4. Run `faster-whisper` on the audio, letting the model detect the spoken language automatically unless the user overrides it.[cite:68][cite:65]
5. Write the transcript as `.srt`, `.vtt`, `.txt`, or `.json` depending on CLI options.[cite:68]
6. If the user requested translation, translate the final transcript into the target language.[cite:64]

## Why this stack

| Problem | Recommended tool | Reason |
|---|---|---|
| YouTube extraction | `yt-dlp` | Mature open-source downloader with subtitle support and broad platform adoption.[cite:8][cite:16] |
| Local multilingual transcription | `faster-whisper` | Faster Whisper implementation built on CTranslate2, practical for local transcription workflows.[cite:68][cite:63] |
| Offline translation | Argos Translate | Open-source and offline, suitable for a no-cloud default design.[cite:64][cite:66] |

This stack is bluntly the most practical open-source version of the workflow the tool needs to support today.[cite:8][cite:68][cite:64]

## User experience

The tool should expose one main command:

```bash
ytx <youtube-url> [options]
```

Basic examples:

```bash
# Official subtitles only; fail if none exist
ytx "https://youtube.com/watch?v=VIDEO_ID" --official-only

# Prefer official subtitles, else transcribe locally
ytx "https://youtube.com/watch?v=VIDEO_ID"

# Prefer official subtitles, else transcribe, then translate to English
ytx "https://youtube.com/watch?v=VIDEO_ID" --to en

# Batch mode
ytx --input urls.txt --to en
```

The default UX should be conservative: prefer official subtitles, do not use auto-generated captions unless `--allow-auto-subs` is set, and only translate when the user opts in.[cite:25][cite:30]

## Command options

| Option | Purpose |
|---|---|
| `--official-only` | Download only official subtitles; error if absent. |
| `--allow-auto-subs` | Permit YouTube auto-generated subtitles as a fallback before transcription.[cite:25][cite:30] |
| `--source-lang <code>` | Prefer a specific source language; otherwise auto-detect during transcription.[cite:68] |
| `--to <code>` | Translate transcript to the target language after subtitle download or transcription.[cite:64] |
| `--format <srt|vtt|txt|json>` | Choose output format. |
| `--model <tiny|base|small|medium|large-v3>` | Select the `faster-whisper` model size, trading speed for quality.[cite:68] |
| `--output <dir>` | Choose output directory. |
| `--keep-audio` | Keep downloaded audio after transcription. |
| `--input <file>` | Read URLs from a text file for batch processing. |
| `--verbose` | Show full internal tool output for debugging. |

## Install strategy

The CLI should install as a normal Python package and manage dependencies in layers.[cite:68][cite:64]

### Required runtime dependencies

- Python 3.10+.
- `yt-dlp` for YouTube extraction.[cite:8][cite:16]
- `faster-whisper` for transcription.[cite:68]
- `argostranslate` for offline translation.[cite:64][cite:69]

### External binaries

`ffmpeg` should be treated as a required system dependency because audio extraction and format handling are much more reliable with it in place.[cite:8][cite:68]

On macOS, the documented install path should be:

```bash
brew install yt-dlp ffmpeg
pip install ytx
```

The CLI may also provide `ytx doctor` to verify that `yt-dlp`, `ffmpeg`, and model downloads are working correctly.[cite:16][cite:68]

## Whisper model behavior

The tool should not bundle Whisper model files in the package. Instead, it should download the selected `faster-whisper` model on first use and cache it locally, because that is how the transcription layer is normally consumed in practice.[cite:68][cite:63]

Recommended default model:

- `small` for normal local use, because it is usually the best balance of speed and quality for a consumer laptop.[cite:68][cite:65]

Other model guidance:

- `tiny` or `base` for speed-first workflows.[cite:68]
- `medium` or `large-v3` when quality matters more than runtime cost.[cite:68]

## Translation behavior

Translation should run on the completed transcript, not on raw subtitle lines one by one, because line-by-line translation usually produces worse phrasing and broken context.[cite:64]

The first version should translate in chunks such as paragraph-like blocks or timestamp groups, then reconstruct the chosen output format.[cite:64]

Important limitation: offline translation is feasible, but it will not consistently match strong cloud LLM translation quality, especially for idioms, slang, or low-resource languages.[cite:64][cite:66]

## Output layout

Suggested output naming:

```text
output/
  video-title/
    source.info.json
    source.original.srt
    source.transcribed.srt
    source.translated.en.srt
    source.translated.en.txt
```

Rules:

- If official subtitles are downloaded, name them `original`.[cite:25]
- If local transcription was used, name that file `transcribed`.[cite:68]
- If translation was run, include the target language code in the filename.[cite:64]
- Preserve timestamps in subtitle outputs unless the user asks for plain text.[cite:68]

## Failure modes

| Scenario | Expected behavior |
|---|---|
| Official subtitles absent | Fall back to audio plus local transcription unless `--official-only` is set.[cite:25][cite:68] |
| `yt-dlp` fails due to site change | Return a clear extraction error and suggest updating `yt-dlp`.[cite:8][cite:21] |
| `ffmpeg` missing | Fail early with a dependency message. |
| Whisper model download fails | Retry once, then return a cache/download error.[cite:68] |
| Translation package for a language pair is unavailable | Return transcript successfully and mark translation as skipped.[cite:64][cite:66] |

## Suggested architecture

```text
ytx/
  cli.py
  config.py
  youtube.py
  subtitles.py
  transcribe.py
  translate.py
  formats.py
  outputs.py
  doctor.py
```

Module responsibilities:

- `cli.py`: argument parsing, command dispatch, exit codes.
- `youtube.py`: `yt-dlp` invocation, metadata inspection, audio download.
- `subtitles.py`: official-vs-auto subtitle selection logic.[cite:25][cite:30]
- `transcribe.py`: `faster-whisper` model loading, language detection, transcript segments.[cite:68]
- `translate.py`: Argos package lookup, install, and translation pipeline.[cite:64][cite:69]
- `formats.py`: conversions between segment structures and `.srt`, `.vtt`, `.txt`, `.json`.
- `outputs.py`: path naming, metadata writing, cleanup rules.
- `doctor.py`: environment checks.

## First release scope

The MVP should include only the features that directly serve the core workflow:[cite:25][cite:68][cite:64]

- Single-video processing.
- Batch processing from a text file.
- Official subtitles preferred by default.
- Local transcription fallback.
- Optional offline translation.
- `srt`, `txt`, and `json` output.
- Clean exit codes and readable errors.

The MVP should exclude playlist support, GUI packaging, speaker diarization, chapter-aware segmentation, and cloud translation providers.[cite:68][cite:64]

## Recommendation

Build this CLI in Python and keep the first version boring. The win is not novelty; the win is a reliable one-command workflow that prefers official subtitles, falls back to local transcription, and optionally translates offline.[cite:8][cite:68][cite:64]

That design is realistic, open-source, and implementable on a Mac without depending on a hosted service.[cite:16][cite:68][cite:64]
