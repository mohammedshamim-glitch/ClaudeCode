# Digital Fusion — Automated YouTube Production Pipeline

Automated end-to-end video production system for the [Digital Fusion](https://www.youtube.com/@TheDigital_Fusion) YouTube channel. Takes a topic idea from research through to a finished, uploaded video — with human approval gates at each stage.

---

## Pipeline Overview

```
Trend Research → Script → Image Prompts → TTS Audio → SEO & Thumbnail → Video Assembly → YouTube Upload
    Stage 1        Stage 2    Stage 3        Stage 4       Stage 5            Stage 6         Stage 7
```

Each stage is a Claude Code skill, invokable as a slash command.

---

## Slash Commands

| Command | What it does |
|---|---|
| `/monkey-finance-pipeline` | Run the full pipeline end-to-end with approval gates |
| `/monkey-finance-trends` | Trend research, competitor analysis, content recommendations |
| `/monkey-finance-scriptwriter` | Write a broadcast-ready narration script |
| `/monkey-finance-tts` | Generate narration audio via Gemini TTS |
| `/monkey-finance-image-prompts` | Generate Grok image prompts + Ken Burns movement file |
| `/monkey-finance-video-creator` | Assemble images + audio into a finished MP4 |
| `/monkey-finance-seo-thumbnail` | Generate SEO title, description, tags, and thumbnail prompt |
| `/monkey-finance-youtube-upload` | Upload the finished video to YouTube with full metadata |

---

## Key Scripts

| Script | Purpose |
|---|---|
| `generate_timings_whisper.py` | Whisper word-level timestamps → `audio_timings_new.csv` |
| `create_video_kb.py` | Assemble images + audio into 1080p MP4 with Ken Burns effects |
| `run_tts.py` | Text-to-speech narration generation |
| `upload_youtube.py` | Upload finished video to YouTube with SEO metadata |
| `setup_youtube_auth.py` | One-time YouTube OAuth setup (full scope) |
| `setup_auth.py` | One-time Google Drive OAuth setup |

---

## Video Assembly

Scene timing is driven by Whisper word-level timestamps — each scene lasts exactly as long as its narration requires, never equal splits.

**Ken Burns effects:** 4 directional pans (left→right, right→left, top→bottom, bottom→top), applied to 25% of scenes.

```bash
# Generate timings from narration audio
python3 generate_timings_whisper.py <episode_folder_id>

# Build video with Ken Burns effects
python3 create_video_kb.py <episode_folder_id>

# Build video without Ken Burns
python3 create_video_kb.py <episode_folder_id> --no-kb
```

---

## Drive Structure

```
Episode Folder/
├── Images/                  ← Scene images, ordered by modifiedTime
├── narration_script.txt     ← Plain text narration (scenes separated by blank lines)
├── narration.mp3            ← TTS audio
├── audio_timings_new.csv    ← Whisper-generated timings
└── <folder name>.mp4        ← Finished video
```

**Known episode folders:**

| Episode | Drive Folder ID |
|---|---|
| S&P 500 vs Picking Your Own Stocks | `1VSu4FuGUQhDxk6yC5HAjnze6YetAEecO` |
| S&P 500 All-Time High During War | `1fFJnQTbnJ6hAKmD5sXDhVFdk77U_f52U` |

---

## Auth Setup

All secrets live in `token.json` (gitignored). Run these once per environment:

```bash
python3 setup_auth.py          # Google Drive access
python3 setup_youtube_auth.py  # YouTube upload + subscriptions
```

---

## Tech Stack

- **Claude Code** — AI orchestration and skill execution
- **Google Drive API** — asset storage and retrieval
- **Gemini TTS** — narration audio generation
- **OpenAI Whisper** — word-level audio timestamps (base model, local)
- **FFmpeg** — video assembly and Ken Burns effects
- **YouTube Data API v3** — video upload and metadata
