---
name: monkey-finance-pipeline
description: >
  Full end-to-end video production orchestrator for the Monkey Finance channel.
  Runs all 6 pipeline stages in order — from trend research to finished MP4 — with
  a human approval gate after each stage so nothing moves forward without sign-off.
  Can also start from any stage if earlier work is already done.
  Use this skill whenever Sham says "run the pipeline", "make a new video", "start the
  pipeline", "full pipeline", "end to end", "produce the video", or "start from Stage X".
  This is the master skill — it delegates to all individual skills in order.
  Never run the full pipeline without this skill.
---

# 🎬 Monkey Finance — Full Production Pipeline

One skill. Six stages. One finished video.

Every Monkey Finance video flows through these stages in order:

| Stage | Skill | Input | Output |
|---|---|---|---|
| **1** | `monkey-finance-trends` | Topic idea or blank | Content brief + winning topic |
| **2** | `monkey-finance-scriptwriter` | Content brief | `02-narration-script-structured.txt` + `03-narration-script-clean.txt` |
| **3** | `monkey-finance-image-prompts` | Clean narration script | `04-image-prompts.txt` + `05-video-prompts.txt` |
| **4** | `monkey-finance-seo-thumbnail` | Script + brief | `06-seo-metadata.txt` |
| **5** | `monkey-finance-tts` | `03-narration-script-clean.txt` | `narration.mp3` |
| **6** | `monkey-finance-video-creator` | Images + `narration.mp3` | `<episode-title>.mp4` |

---

## How to Start

### Full pipeline from scratch
> "Run the full pipeline" / "Make a new video" / "Start the pipeline"

Ask Sham: *"Do you have a topic in mind, or shall I run a trend sweep to find the best one?"*

- If he has a topic → skip Stage 1, go straight to Stage 2 with the topic as brief input
- If no topic → run Stage 1 first

### Starting from a specific stage
> "Start from Stage 3" / "I already have a script, go from image prompts"

Jump directly to that stage. Confirm what Drive assets already exist before proceeding.

---

## Drive Folder Setup

The episode folder is created **automatically after the topic is approved** at the end of Stage 1 (or immediately if Sham provides a topic directly and skips Stage 1).

### Auto-create the folder
Use the Drive `create_file` tool with:
- `title`: `YYYY-MM-DD - <Episode Title>` (use today's date, format the title cleanly)
- `mimeType` (set as the file's mime type): `application/vnd.google-apps.folder`
- `parentId`: `1Z-aB7dKK9T9EpndozU-6lAvbxdo6yknS` (Monkey Finance root)

Example folder name: `2026-05-03 - S&P 500 vs Buying a House`

Confirm creation with: *"Drive folder created: `YYYY-MM-DD - <Episode Title>` — [folder link]. All pipeline files will be saved here."*

Store the returned folder ID — every subsequent stage saves its output files into this folder.

### If folder already exists
Search Drive first. If Sham says the folder is already there, get its ID before proceeding rather than creating a duplicate.

---

## Stage-by-Stage Process

### ▶ STAGE 1 — Trend Research
**Skill:** `monkey-finance-trends`

Run the full trend sweep: 6 phases, scored opportunities, full content brief for the top pick.

**Approval gate:**
> *"Stage 1 complete. Here are the top 3 opportunities with scores. My recommendation is [X] — confidence [Y/10]. Shall I run the pipeline with this topic, or do you want to pick a different one?"*

Wait for Sham's go-ahead. Once topic is confirmed → **create the Drive folder automatically** before moving to Stage 2.

---

### ▶ STAGE 2 — Script Writing
**Skill:** `monkey-finance-scriptwriter`

Write the full narration script using the approved topic/brief. 4-pass method. 1,400–1,600 words. 25-word scenes. Save both files to Drive.

**Approval gate:**
> *"Stage 2 complete. Script saved to Drive — [link]. Word count: [X]. Want to punch up any section, or shall we move to image prompts?"*

Wait for Sham's approval (and any edits) before Stage 3.

---

### ▶ STAGE 3 — Image Prompts
**Skill:** `monkey-finance-image-prompts`

Parse the clean narration script into sub-scenes (~25 words each). Generate `04-image-prompts.txt` and `05-video-prompts.txt`. Save both to Drive.

**Approval gate:**
> *"Stage 3 complete. [X] image prompts and video prompts saved to Drive — [link]. Review the prompts and confirm you're happy with the visuals before I continue to SEO."*

Wait for Sham's approval before Stage 4.

---

### ▶ STAGE 4 — SEO & Thumbnail
**Skill:** `monkey-finance-seo-thumbnail`

Generate the full Click Package: 3 title variants, description, tags, hashtags, chapters, thumbnail brief, and Grok thumbnail prompt. Save as `06-seo-metadata.txt` to Drive.

**Approval gate:**
> *"Stage 4 complete. SEO package saved to Drive — [link]. Primary title: '[title]'. Want to tweak anything, or shall I generate the audio next?"*

Wait for Sham's approval before Stage 5.

---

### ▶ STAGE 5 — Audio Generation (TTS)
**Skill:** `monkey-finance-tts`

Run TTS on `03-narration-script-clean.txt`. Upload `narration.mp3` to the episode Drive folder.

```bash
python3 /home/user/ClaudeCode/run_tts.py <narration_file_id> <episode_folder_id> narration.mp3
```

**Approval gate:**
> *"Stage 5 complete. `narration.mp3` uploaded to Drive. Audio is [X] minutes [Y] seconds. Ready to build the video — with or without Ken Burns effects?"*

Wait for Sham's Ken Burns preference before Stage 6.

---

### ▶ STAGE 6 — Video Assembly
**Skill:** `monkey-finance-video-creator`

1. Generate smart timing CSV:
```bash
python3 /home/user/ClaudeCode/generate_timings.py <episode_folder_id>
```

2. Create the video (with or without Ken Burns per Sham's choice):
```bash
# With Ken Burns (default)
python3 /home/user/ClaudeCode/create_video_kb.py <episode_folder_id>

# Without Ken Burns
python3 /home/user/ClaudeCode/create_video_kb.py <episode_folder_id> --no-kb
```

**Pipeline complete:**
> *"Pipeline complete. `<episode-title>.mp4` uploaded to Drive — [link]. All 6 stages done. Ready to upload to YouTube using the SEO package from Stage 4."*

---

## Approval Gate Rules

- **Never skip a gate** — every stage requires explicit confirmation before proceeding
- **Edits reset the downstream** — if Sham edits the script at Stage 2, image prompts (Stage 3) must be regenerated
- **Partial re-runs are fine** — if only one stage needs a redo, re-run just that stage and continue forward
- **Always show the Drive link** after each stage so Sham can review the file directly

---

## Quick Reference — Drive Folder IDs

| Channel | Drive Folder ID |
|---|---|
| Monkey Finance | `1Z-aB7dKK9T9EpndozU-6lAvbxdo6yknS` |
| Monkey See Money | `1N0fFEokv69CVVMbSFbIi_FFDsab3kadR` |

---

## Shortcut Entry Points

| What Sham says | Start at |
|---|---|
| "Run the pipeline" / "Make a video" | Stage 1 (or Stage 2 if topic given) |
| "I have a brief, write the script" | Stage 2 |
| "Script's done, make the image prompts" | Stage 3 |
| "Generate the SEO" | Stage 4 |
| "Generate the audio" | Stage 5 |
| "Build the video" | Stage 6 |

---

*Individual skill docs: `monkey-finance-trends` · `monkey-finance-scriptwriter` · `monkey-finance-image-prompts` · `monkey-finance-seo-thumbnail` · `monkey-finance-tts` · `monkey-finance-video-creator`*
