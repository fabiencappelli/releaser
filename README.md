# Release Video Generator

![status](https://img.shields.io/badge/status-experimental-blue)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![ffmpeg](https://img.shields.io/badge/ffmpeg-required-orange)

A small Python pipeline that converts **release notes exported from Jira** into a **narrated slide video**.

The tool parses an HTML export of selected Jira issues, generates a structured script, produces narration using text-to-speech, and renders a simple slide video automatically.

The goal is to quickly transform technical release information into a **short, easy-to-consume update video**.

---

# Overview

The pipeline performs three main steps:

1. **Parse release notes**
2. **Generate a video script**
3. **Produce audio and render slides**

The result is a short video presenting the key changes in a release.

```
Jira Export (HTML)
        │
        ▼
 Script Generation
        │
        ▼
 Voice Narration
        │
        ▼
 Slide Rendering
        │
        ▼
   Final Video
```

---

# Input Format

The pipeline expects an **HTML export from Jira**.

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

This file is placed in:

```
data/
```

Example:

```
data/release_export.html
```

The parser extracts the relevant information from this file to build the script.

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

---

# Project Structure

```
project/
│
├─ assets/                # visual assets (background image)
│   └─ background.png
│
├─ audio/                 # generated narration audio
│   └─ .gitkeep
│
├─ build/                 # intermediate artifacts
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
│   └─ render_video.py
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
pip install openai
```

Set your API key:

```
export OPENAI_API_KEY=your_key_here
```

---

# Running the Pipeline

The pipeline runs in three steps.

---

## 1 Generate the script

```
python src/generate_script.py
```

This step:

- parses the Jira HTML export
- extracts relevant issue information
- generates a structured JSON script

Output:

```
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

## 3 Render the video

```
python src/render_video.py
```

This step:

- renders slide visuals
- overlays text onto a background image
- synchronizes with narration
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

This project automates the transformation from **release notes to video presentation**.

---

# Limitations

Current version:

- static background image
- simple slide layout
- no animations

Possible future improvements:

- slide transitions
- progress bar
- subtitles
- background music
- dynamic layouts

---

# License

Provided for experimentation and learning purposes.
