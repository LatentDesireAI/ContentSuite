# ContentSuite

Public desktop app for Windows that prepares images and video for **Patreon**, **Pixiv**, and **X**.

Free to download and use. Built for creators who publish on multiple platforms.

## Features

### Images
- Batch PNG/JPG → JPEG compression
- Metadata stripping (including ComfyUI / A1111 prompt chunks)
- Multi-page PDF export
- Grid selection for partial batches
- Optional original filenames on export

### Pixiv Preview
- Collage cover from 1–3 artworks on a white background
- Layout presets and frame styling

### Video
- Watermark overlay (position, opacity, size)
- Convert to mp4 / webm / mov
- GIF export
- Ugoira export (frames + `animation.json`)
- Clip grid with hover preview and audio
- Metadata removal, audio on/off

### Pixiv Censor
- Blur/block censoring on video with manual zone editor

Settings (folders, watermarks, quality, author EXIF) are stored in `%APPDATA%\ContentSuite\config.json`.

## Requirements

- Windows 10/11
- [Python](https://www.python.org/downloads/) 3.11+
- [ffmpeg](https://ffmpeg.org/) and `ffprobe` in `PATH`

## Quick start

```bat
run.bat
```

`run.bat` creates a local `.venv`, installs dependencies, and launches the GUI.

Manual setup:

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pythonw main.py
```

## Project layout

```
main.py              — application entry point
tabs/                — UI tabs (images, video, pixiv preview, censor)
core/                — compression, ffmpeg, watermark, config, PDF
ui/                  — reusable widgets (grids, dialogs, pickers)
```

## Authors

**[LatentDesireAI](https://github.com/LatentDesireAI)** — creator & maintainer

**AI-Assisted** — co-development with [Grok (xAI)](https://x.ai) via [Cursor](https://cursor.com)