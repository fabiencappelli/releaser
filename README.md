# Release Video Generator

![status](https://img.shields.io/badge/status-experimental-blue)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![ffmpeg](https://img.shields.io/badge/ffmpeg-required-orange)

A small Python pipeline that converts **release notes exported from Jira** into a **narrated slide video**.

The tool parses an HTML export of selected Jira issues, uses optional curated release notes to preserve high-level topic grouping, generates a structured script, produces narration using text-to-speech, and renders a simple slide video automatically.

The goal is to quickly transform technical release information into a **short, easy-to-consume update video**.

---

# Overview

The pipeline performs four main steps:

1. **Parse release notes**
2. **Generate a video script**
3. **Generate narration audio**
4. **Render slides and assemble the final video**

The result is a short narrated video presenting the key changes in a release.

```
Jira Export (HTML)
        │
        ├── Release Notes (Markdown, optional)
        │
        ▼
 Theme + Script Generation
        │
        ▼
 Voice Narration
        │
        ▼
 Audio Normalization
        │
        ▼
 Slide Rendering
        │
        ▼
   Final Video
```

In version 2, the audio pipeline was redesigned to improve **synchronization reliability** between narration and slides.

In version 3, the generation pipeline was updated to improve release-level storytelling and reduce slide fragmentation:

- `data/release_notes.md` can now guide theme grouping from already-curated release notes.
- Theme generation and script generation now use separate configurable OpenAI models.
- The default models are `gpt-5.4-nano` for theme grouping and `gpt-5.4-mini` for script writing.
- Script generation now favors one content slide per broader release theme instead of one small chapter per ticket.
- Text-to-speech now uses the `marin` voice for a more natural narration style.
- Slide titles are wrapped, resized, and truncated when needed to avoid overflowing their visual frame.

---

# Input Format

The pipeline expects an **HTML export from Jira** and can optionally use a curated **Markdown release notes** file.

Typical workflow:

1. Open an issue search in Jira
2. Select the columns you want to include
3. Export the result as **HTML**

Recommended columns:

- Key
- Summary
- Description
- Issue Type
- Labels
- Status

The export should contain only the issues relevant to the release.

The Jira export is placed in:

```
data/jira_export.html
```

The parser extracts the relevant ticket information from this file.

Optional release notes guide:

```
data/release_notes.md
```

When present, `release_notes.md` is passed to the script-generation model as an editorial guide. It should already group Jira tickets into release-level themes. The model uses it to avoid generating too many small chapters while still treating the Jira export as the source of truth for ticket details and available ticket keys.

---

# Example Output

The generated video consists of a sequence of narrated slides.

Example slide layout:

```
Advanced API Filtering

• Filters on transactions and events
• Support for date and entity criteria
• Improved validation and error handling
```

Each slide:

- shows a short title
- displays 2–4 bullet points
- plays a narration explaining the change

Short pauses between slides improve readability.

---

# Project Structure

```
project/
│
├─ assets/                # visual assets (background image)
│   └─ background.png
│
├─ audio/                 # generated narration audio (mp3)
│   └─ .gitkeep
│
├─ build/                 # intermediate artifacts
│   ├─ normalized_audio/  # normalized WAV narration
│   └─ .gitkeep
│
├─ output/                # final video
│   └─ .gitkeep
│
├─ data/                  # input data (Jira exports)
│   └─ .gitkeep
│
├─ src/
│   ├─ generate_script.py
│   ├─ generate_audio.py
│   ├─ build_audio_track.py
│   ├─ render_video.py
│   └─ run_all.py
│
├─ .gitignore
└─ README.md
```

Generated files are intentionally excluded from version control.

---

# Requirements

Python 3.10+

System dependency:

```
ffmpeg
```

Install on Ubuntu:

```
sudo apt install ffmpeg
```

---

# Python Setup

Create a virtual environment:

```
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Set your API key:

```
export OPENAI_API_KEY=your_key_here
```

Optional model overrides:

```
export OPENAI_THEME_MODEL=gpt-5.4-nano
export OPENAI_SCRIPT_MODEL=gpt-5.4-mini
```

Defaults:

- `OPENAI_THEME_MODEL`: `gpt-5.4-nano`
- `OPENAI_SCRIPT_MODEL`: `gpt-5.4-mini`
- TTS model: `gpt-4o-mini-tts`

---

# Running the Pipeline

You can run the pipeline **step-by-step** or use the **automatic runner**.

---

# Quick Run (recommended)

```
python src/run_all.py
```

This executes the full pipeline:

1. Generate script
2. Generate narration audio
3. Build the final audio track (with pauses)
4. Render the final video

---

# Manual Execution

## 1 Generate the script

```
python src/generate_script.py
```

This step:

- reads parsed Jira ticket data from `build/release_structured.json`
- reads `data/release_notes.md` when present
- groups tickets into broader release themes
- generates a structured JSON script with one content slide per theme

Output:

```
build/themes.json
build/script.json
```

Example segment:

```
{
  "id": "example_feature",
  "title": "Example Feature",
  "on_screen_text": [
    "First bullet",
    "Second bullet",
    "Third bullet"
  ],
  "voiceover": "Narration text explaining the change."
}
```

---

## 2 Generate narration audio

```
python src/generate_audio.py
```

This creates audio narration for each segment.

Output example:

```
audio/00_intro.mp3
audio/01_feature.mp3
audio/02_update.mp3
```

---

## 3 Build the final audio track

```
python src/build_audio_track.py
```

This step:

- converts MP3 narration to **normalized WAV audio**
- inserts **silent pauses between slides**
- concatenates all audio segments

Final output:

```
build/final_audio.wav
```

The normalization step improves synchronization between slides and narration.

---

## 4 Render the video

```
python src/render_video.py
```

This step:

- renders slide visuals
- overlays text onto a background image
- synchronizes slides with narration
- concatenates all segments

Final output:

```
output/release.mp4
```

---

# Customization

## Background image

Replace:

```
assets/background.png
```

with any image.

---

## Slide styling

Adjust parameters in:

```
src/render_video.py
```

For example:

- font size
- slide margins
- panel opacity
- video resolution
- pause duration between slides

---

# Git Notes

This repository excludes generated or sensitive artifacts.

Ignored by `.gitignore`:

- audio files
- build artifacts
- rendered videos
- local input data

Folder structure is preserved using `.gitkeep`.

---

# Why This Tool Exists

Release notes are often long and difficult to digest.

Short narrated videos can help communicate updates to:

- product teams
- developers
- internal stakeholders
- users

This project automates the transformation from **release notes to a narrated video presentation**.

---

# Limitations

Current version:

- static background image
- simple slide layout
- no animations
- limited slide templates

Possible future improvements:

- slide transitions
- subtitles
- background music
- dynamic layouts
- multiple visual themes

---

# License

Provided for experimentation and learning purposes.
