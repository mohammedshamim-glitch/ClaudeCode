---
name: mala-maya-pipeline
description: >
  Full end-to-end video production orchestrator for the Maya & Mala Kids channel.
  Supports two content paths: Path A (Children's Story) and Path B (Nursery Song).
  Runs all steps in order with a human approval gate after each one.
  Use this skill whenever the user says "run the pipeline", "make a new video", "start
  from step X", "produce the video", "Path A", "Path B", or any variation meaning
  start or continue the Mala and Maya video production process.
  This is the master skill — it delegates to all individual mala-maya skills in order.
---

# 🎬 Maya & Mala Kids — Full Production Pipeline

Two paths. One finished video. Every step requires approval before proceeding.

---

## PRE-STEP: Choose Your Content Type

At the start of every new project, confirm two things:

**1. Content path:**
- **Path A — Children's Story**: original story, narration audio via Gemini TTS (Aoede voice)
- **Path B — Nursery Song**: original lyrics, full song generated manually via Suno

**2. Character option:**
- **Include Maya & Mala** (default): feature both characters by name throughout
- **No named characters**: use "you", "we", "friends", or generic child figures

→ Ask if not stated: *"Path A (story) or Path B (nursery song)? And shall I include Maya & Mala as named characters?"*

---

## Pipeline Overview

| Step | Skill | Output |
|---|---|---|
| **0** | `mala-maya-trends` | 3–5 topic options |
| **1** | `mala-maya-scriptwriter` | `01_story_approved.txt` or `01_song_lyrics_approved.txt` |
| **2A** | `mala-maya-image-prompts` | `02_image_prompts.txt` |
| **2B** | `mala-maya-video-prompts` | `02_video_prompts.txt` |
| **3** | `mala-maya-seo` | `03_youtube_seo.txt` + `03_thumbnail_prompt.txt` |
| **4A** (Path A) | Gemini TTS | `04_story_audio.mp3` |
| **4B** (Path B) | Suno (manual) | `04_song_audio.mp3` |
| **5** | `shared/youtube-upload` | Published YouTube video |

---

## Drive Folder Setup

**Root folder:** Mala and Maya (ID: `17FIaircel64AqXwAlCafF7Lhv94TQGNk`)

Create a new episode subfolder immediately after Step 0 (topic approved):
- `title`: project name slug (e.g. `Hop-Little-Bunnies`)
- `mimeType`: `application/vnd.google-apps.folder`
- `parentId`: `17FIaircel64AqXwAlCafF7Lhv94TQGNk`

Store the returned folder ID — all subsequent steps save files here.

---

## Step-by-Step Process

### ▶ STEP 0 — Research Trending Topics
**Skill:** `mala-maya-trends`

Research trending children's content for the chosen path. Propose 3–5 options with brief descriptions. Wait for approval before proceeding.

**Approval gate:**
> *"Here are 3–5 topic options. Which one shall we go with?"*

Once approved: create the Drive episode folder and confirm the link.

---

### ▶ STEP 1 — Write Story or Lyrics
**Skill:** `mala-maya-scriptwriter`

- **Path A:** 18+ scenes, ~7 min duration, engaging arc, age-appropriate
- **Path B:** 18+ sections, Intro → Verses/Choruses/Bridges → Outro, one action per section

Output: `01_story_approved.txt` (Path A) or `01_song_lyrics_approved.txt` (Path B) — saved to Drive.

**Approval gate:**
> *"Story/lyrics written and saved to Drive — [link]. Happy with this, or shall we adjust anything before moving to image prompts?"*

---

### ▶ STEP 2A — Image Prompts
**Skill:** `mala-maya-image-prompts`

One visual description per scene (18+ entries). Disney/Pixar style. Output: `02_image_prompts.txt` — saved to Drive.

**Approval gate:**
> *"Image prompts saved to Drive — [link]. Ready for video prompts?"*

---

### ▶ STEP 2B — Video Prompts
**Skill:** `mala-maya-video-prompts`

One entry per scene, two lines each: visual + camera movement. Output: `02_video_prompts.txt` — saved to Drive.

**Approval gate:**
> *"Video prompts saved to Drive — [link]. Moving to SEO."*

---

### ▶ STEP 3 — YouTube SEO + Thumbnail Prompt
**Skill:** `mala-maya-seo`

Title, description, tags, hashtags, kids category settings, end screen suggestions, thumbnail prompt. Two files saved to Drive: `03_youtube_seo.txt` + `03_thumbnail_prompt.txt`.

**Approval gate:**
> *"SEO package saved to Drive — [link]. To generate the thumbnail: go to grok.com/imagine → paste the prompt from `03_thumbnail_prompt.txt` → set ratio 16:9 → save as `thumbnail` in the episode folder. Ready for audio when you are."*

---

### ▶ STEP 4 — Audio Generation

**Path A — Narration via Gemini TTS:**
```bash
python3 /home/user/ClaudeCode/run_tts.py <script_file_id> <episode_folder_id> 04_story_audio.mp3
```
Voice: `Aoede` (female, warm, Disney-like). Output: `04_story_audio.mp3` — uploaded to Drive.

**Path B — Song via Suno (manual):**
1. Go to suno.com → Custom Mode
2. Paste lyrics from Step 1
3. Style: `children's nursery rhymes, playful, fun and sing along, upbeat, bouncy, whimsical, kids pop`
4. Generate 2 variations, pick the best
5. Download and upload to Drive as `04_song_audio.mp3`

**Approval gate:**
> *"Audio confirmed in Drive. Ready to assemble the video or upload directly?"*

---

### ▶ STEP 5 — Upload to YouTube
**Skill:** `shared/youtube-upload`

Use `03_youtube_seo.txt` for metadata. Category: Kids & Family. Language: en-GB. Thumbnail: named `thumbnail` in the episode folder.

**Approval gate:**
> *"Pipeline complete. Video uploaded/scheduled. All steps done."*

---

## Approval Gate Rules

- **Never skip a gate** — every step requires explicit confirmation before proceeding
- **Edits at Step 1 require Steps 2A and 2B to be regenerated** — image/video prompts must match the approved story/lyrics
- **Partial re-runs are fine** — re-run just the affected step and continue forward
- **Always show the Drive link** after each step so the file can be reviewed directly

---

## Quick Reference

| What's said | Start at |
|---|---|
| "Run the pipeline" / "Make a new video" | Step 0 (or Step 1 if topic given) |
| "Write the story/lyrics" | Step 1 |
| "Make the image prompts" | Step 2A |
| "Make the video prompts" | Step 2B |
| "Generate the SEO" | Step 3 |
| "Generate the audio" | Step 4 |
| "Upload to YouTube" | Step 5 |

---

*Individual skills: `mala-maya-trends` · `mala-maya-scriptwriter` · `mala-maya-image-prompts` · `mala-maya-video-prompts` · `mala-maya-seo` · `shared/youtube-upload`*
