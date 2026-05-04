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

| Stage | Skill | Input | Drive Output |
|---|---|---|---|
| **1** | `monkey-finance-trends` | Topic idea or blank | `01-trend-report.md` |
| **2** | `monkey-finance-scriptwriter` | Content brief | `02-narration-script-structured.txt` + `03-narration-script-clean.txt` |
| **3** | `monkey-finance-image-prompts` | Clean narration script | `04-image-prompts.txt` + `05-video-prompts.txt` |
| **4** | `monkey-finance-seo-thumbnail` | Script + brief | `06-seo-metadata.txt` |
| **5** | `monkey-finance-tts` | `03-narration-script-clean.txt` | `narration.mp3` |
| **6** | `monkey-finance-video-creator` | Images + `narration.mp3` | `<episode-title>.mp4` |
| **7** | Analytics review | YouTube Studio data | `07-analytics-review.md` |

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

Wait for Sham's go-ahead. Once topic is confirmed:
1. **Create the Drive folder** (see Drive Folder Setup above)
2. **Save the full trend report** to the folder as `01-trend-report.md` — includes market snapshot, all scored opportunities, evergreen picks, and the winning content brief
3. Confirm: *"Drive folder created and trend report saved — [folder link]. Moving to Stage 2."*

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

### ▶ STAGE 7 — Analytics Review (7–14 days after publish)

**When to run:** 7 days after the video goes live on YouTube. Run again at 14 days for a fuller picture.

**Trigger:** Sham says "review the video performance", "check the analytics", "how did the video do", or 7+ days have passed since publish and he asks about the video.

**Goal:** Extract performance data, identify what worked and what didn't, and feed the learnings directly into the next trend report and script.

#### Metrics to Review

Ask Sham to share or check the following from YouTube Studio Analytics:

| Metric | Where to find | Target benchmark |
|---|---|---|
| **Impressions CTR** | Analytics → Reach | 4–6% solid, 6%+ excellent |
| **Average view duration** | Analytics → Engagement | 50%+ of video length |
| **Average % viewed** | Analytics → Engagement | 50%+ |
| **Top traffic source** | Analytics → Reach → Traffic source | Search, Suggested, or Browse |
| **A/B title winner** | Test & Compare results | Which variant won and by how much? |
| **Subscribers gained** | Analytics → Audience | Net new from this video |
| **Top drop-off point** | Analytics → Engagement → Key moments | Which timestamp lost viewers? |

#### Four Questions to Answer

1. **Did the packaging work?** (CTR above or below benchmark?)
   - Above 6% → packaging is strong, topic was right
   - 4–6% → acceptable, minor tweaks to thumbnail or title
   - Below 4% → packaging failed — the hook, thumbnail, or topic didn't land

2. **Did the content work?** (Average view duration above or below 50%?)
   - Above 50% → script held attention well
   - 40–50% → retention dipped — check the drop-off timestamp and identify which section lost viewers
   - Below 40% → script or pacing issue — flag for scriptwriter review

3. **Where did the traffic come from?**
   - High Search traffic → SEO is working, topic had real search demand
   - High Suggested traffic → algorithm liked it, thumbnail/title earned the push
   - High Browse traffic → existing subscribers watched, but the video didn't grow the channel

4. **What did the A/B title test reveal?**
   - Which emotional hook won? Record this — it tells you how your audience responds
   - Fear/warning, curiosity, or aspiration? Build this into the next video's packaging

#### Analytics Review Output

Save a brief `07-analytics-review.md` to the episode Drive folder with:

```markdown
# Analytics Review — [Episode Title]

**Review date:** [date] ([X] days after publish)

## Key Numbers
- CTR: [X]% ([above/below] benchmark)
- Avg view duration: [X]% ([above/below] 50% target)
- Top traffic source: [Search / Suggested / Browse]
- Subscribers gained: [X]
- A/B winner: [Primary / Alt A / Alt B] by [X]% CTR

## What Worked
- [1–2 sentences on what drove performance]

## What Didn't Work
- [1–2 sentences on what underperformed and why]

## Key Drop-Off Point
- [Timestamp] — [Which section of the script this corresponds to]

## Learnings for Next Video
- Packaging: [What to do differently or keep the same]
- Script: [Any structural changes based on drop-off data]
- Topic/SEO: [Did the traffic source match what we expected?]
- Emotional hook: [Which title hook won — apply to next packaging]
```

**After saving:** Feed the learnings summary into the next trend report as context. The channel that learns fastest from its own data wins.

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
