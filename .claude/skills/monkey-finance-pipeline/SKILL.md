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

One skill. Ten stages. One finished video.

Every Monkey Finance video flows through these stages in order:

| Stage | Skill | Input | Drive Output |
|---|---|---|---|
| **1** | `monkey-finance-trends` | Topic idea or blank | `01-trend-report.md` |
| **2** | `monkey-finance-scriptwriter` | Content brief | `02-narration-script-structured.txt` + `03-narration-script-clean.txt` |
| **3** | `monkey-finance-image-prompts` | Clean narration script | `04-image-prompts.txt` + `00b-character-references.txt` (if named chars) |
| **4** | `monkey-finance-tts` | `03-narration-script-clean.txt` | `narration.mp3` |
| **5a** | `monkey-finance-seo-thumbnail` | Script + `audio_timings_new.csv` | `06-seo-metadata.txt` (inc. community post) + `07-thumbnail-prompt.txt` |
| **5b** | `monkey-finance-video-creator` | Images + `narration.mp3` + `audio_timings_new.csv` | `<episode-title>.mp4` |
| **7** | `monkey-finance-youtube-upload` | MP4 + `06-seo-metadata.txt` + thumbnail | Published/scheduled YouTube video |
| **8→9** | Shorts + Wrap Up | Main episode MP4 | `short_preview_vX.mp4` → YouTube Short → folder moved to Completed |
| **10** | Analytics review | YouTube Studio data | `09-analytics-review.md` |

**yt-dlp is used at Stage 1** — pulling live YouTube data during trend research. Competitor tags for SEO are pulled via the YouTube Data API at Stage 5a (yt-dlp is SSL-blocked on this server).

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
- `parentId`: `1N0fFEokv69CVVMbSFbIi_FFDsab3kadR` (Monkey See Money root — default)

Example folder name: `2026-05-03 - S&P 500 vs Buying a House`

Confirm creation with: *"Drive folder created: `YYYY-MM-DD - <Episode Title>` — [folder link]. All pipeline files will be saved here."*

Store the returned folder ID — every subsequent stage saves its output files into this folder.

**Immediately after creating or locating the folder, update CLAUDE.md** — add or update the episode row in the Known Drive Folder IDs table with the exact folder ID returned by Drive. Do this before saving any pipeline files. This prevents wrong-folder errors in future sessions.

### If folder already exists
Search Drive first. If Sham says the folder is already there, get its ID before proceeding rather than creating a duplicate. Never rely on the folder ID cached in CLAUDE.md without confirming via a Drive search — folder IDs can be wrong if CLAUDE.md was not updated when the folder was created.

---

## Stage-by-Stage Process

### ▶ STAGE 1 — Topic Selection

**Always start by asking Sham which route he wants:**

> *"Two options for finding the next topic:*
> *1. Adapt a Wealth Logic video — find their best recent video, extract the transcript via Gemini, and adapt it to UK. Proven structure, faster turnaround.*
> *2. Full trend sweep — research what's performing across finance YouTube right now, score opportunities, and pick the best original angle.*
> *Which do you want to go with?"*

Wait for Sham's choice before doing anything else.

---

#### Route 1 — Wealth Logic Adaptation

1. Use the YouTube Data API to find Wealth Logic's most recent or best-performing videos:
```
GET https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=CHANNEL_ID&order=viewCount&type=video
Authorization: Bearer {youtube_access_token}
```
2. Present the top 3–5 videos with view counts and titles. Ask Sham to pick one.
3. Extract the transcript via Gemini:
```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}
Body: {"contents": [{"parts": [{"text": "Please provide a full word-for-word transcript of this YouTube video."}, {"file_data": {"mime_type": "video/*", "file_uri": "https://www.youtube.com/watch?v=VIDEO_ID"}}]}]}
```
4. Save transcript to Drive as `00-source-transcript-wealth-logic-original.txt`.
5. Analyse the transcript (hook structure, emotional arc, Grand Payoff, analogies).
6. Propose the UK-adapted angle and get Sham's sign-off before writing.
7. Create the Drive folder, update CLAUDE.md, then move to Stage 2.

**Approval gate:**
> *"Here are Wealth Logic's top videos: [list]. Which one do you want to adapt?"*
> Then after transcript analysis: *"Here's the UK angle I'd take: [summary]. Happy to proceed?"*

---

#### Route 2 — Full Trend Sweep
**Skill:** `monkey-finance-trends`

Run the full trend sweep: Phase 0 (yt-dlp live data) + 6 phases + competitor transcript analysis. Produces scored opportunities and a full content brief with competitive differentiation note.

**Approval gate:**
> *"Stage 1 complete. Top picks:*
> *1. [Topic A] — Score: [X/25] — [One-line reason]*
> *2. [Topic B] — Score: [X/25] — [One-line reason]*
> *3. [Topic C] — Score: [X/25] — [One-line reason]*
> 
> *My recommendation: Option [N] — confidence [Y/10]. Which one do you want to run with?"*

Wait for Sham's go-ahead. Once topic is confirmed:
1. **Create the Drive folder** (see Drive Folder Setup above)
2. **Save the full trend report** to the folder as `01-trend-report.md`
3. Confirm: *"Drive folder created and trend report saved — [folder link]. Moving to Stage 2."*

---

### ▶ STAGE 2 — Script Writing
**Skill:** `monkey-finance-scriptwriter`

Write the full narration script using the approved topic/brief. 4-pass method. 1,900–2,100 words. 25-word scenes (min 20, max 35). Save both files to Drive.

**Approval gate:**
> *"Stage 2 complete. Script saved to Drive — [link]. Word count: [X]. Want to punch up any section, or shall we move to image prompts?"*

Wait for Sham's approval (and any edits) before Stage 3.

---

### ▶ STAGE 3 — Image Prompts
**Skill:** `monkey-finance-image-prompts`

Parse the clean narration script into sub-scenes (~25 words each). Generate `04-image-prompts.txt`. Save to Drive.

**Image prompt rules (non-negotiable):**
- Opening line: `2D colourful whiteboard animation style. Clean white background.`
- Second line: `All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges.`
- Never specify monkey suit colour
- Never say "cartoon monkey" — always just "monkey"
- Every monkey scene must show the monkey mid-action with a prop — never just standing

**Approval gate:**
> *"Stage 3 complete. [X] image prompts and media prompts saved to Drive — [link]. Review the prompts and confirm you're happy with the visuals before I continue to audio."*

Wait for Sham's approval before Stage 4.

---

### ▶ STAGE 4 — Audio Generation (TTS) + Subtitles
**Skill:** `monkey-finance-tts`

**Step 4a — Generate audio:**
```bash
python3 /home/user/ClaudeCode/run_tts.py <narration_file_id> <episode_folder_id> narration.mp3
```

No SRT generation needed — YouTube auto-generates en-GB captions when `defaultAudioLanguage` is set to `en-GB` on upload (handled automatically by `upload_youtube.py`).

**Approval gate:**
> *"Stage 4 complete. `narration.mp3` ([X]m [Y]s) uploaded to Drive. Ready to move to Whisper timings + SEO."*

Wait for Sham's approval before Stage 5.

---

### ▶ STAGE 5a — Timings + SEO + Community Post (run together, before video assembly)

**Run all three in parallel immediately after TTS is approved — do not wait for video assembly.**

**Timings:**
```bash
python3 /home/user/ClaudeCode/generate_timings.py <episode_folder_id>
```
This produces `audio_timings_new.csv` — exact per-scene timestamps via aeneas forced alignment. Used for chapter markers in SEO and for video assembly.

**SEO (run at the same time as timings):**
Run `monkey-finance-seo-thumbnail` skill using the narration script. Use the exact timestamps from `audio_timings_new.csv` for chapter markers (or estimate from script structure if timings aren't ready yet — update when CSV lands).

Save `06-seo-metadata.txt` and `07-thumbnail-prompt.txt` to Drive.

**Community post (draft at the same time as SEO):**
Draft the YouTube Community post while writing the SEO package — both pull from the same script. Format:

```
[1–2 sentence hook — something counterintuitive or surprising from the video]

[1 sentence payoff or teaser — what the video reveals]

Full video is live now 👇 [video URL — add after upload]

[Engaging question tied to the topic]
```

Include the community post draft in `06-seo-metadata.txt` under a `COMMUNITY POST` section. Post manually in YouTube Studio → Community tab on the day the video goes live.

**Why before video assembly:** SEO, community post, and thumbnail can all be reviewed while Grok renders the thumbnail — nothing is blocked. Upload day is a single step.

**Approval gate:**
> *"Stage 5a complete. Timings, SEO package, and community post draft saved to Drive — [links]. Generate the thumbnail in Grok using 07-thumbnail-prompt.txt and save it to Drive as 'thumbnail'. Ready to move to video assembly."*

Wait for Sham's approval (and thumbnail confirmation) before Stage 5b.

---

### ▶ STAGE 5b — Video Assembly
**Skill:** `monkey-finance-video-creator`

`audio_timings_new.csv` is already in Drive from Stage 5a — do NOT re-run `generate_timings.py` here. Only re-run it if `narration.mp3` was regenerated after Stage 5a.

Create the video with subtitles:
```bash
python3 /home/user/ClaudeCode/create_video_kb.py <episode_folder_id> --subs
```

This produces `<episode-title>.mp4` and `audio_timings_new.csv` — both uploaded to Drive.

**KB effect rules:**
- Cosine ease-in/ease-out on all effects
- Zoom-in only fires on scenes ≤8s — longer scenes automatically swap to pan bottom→top

**Approval gate:**
> *"Stage 5b complete. Video assembled and uploaded to Drive — [link]. SEO and thumbnail were generated at Stage 5a — confirm thumbnail is saved to Drive as 'thumbnail' and we'll go straight to upload."*

---

### ▶ STAGE 7 — YouTube Upload
**Skill:** `monkey-finance-youtube-upload`

**Pre-upload checklist — confirm all four before running:**
- [ ] `06-seo-metadata.txt` in Drive ✓ (Stage 5a)
- [ ] `07-thumbnail-prompt.txt` in Drive ✓ (Stage 5a)
- [ ] Thumbnail generated in Grok and saved to Drive as `thumbnail` ✓
- [ ] Video assembled and in Drive ✓ (Stage 5b)

If SEO wasn't done at 5a for any reason, run `monkey-finance-seo-thumbnail` now before upload.

```bash
python3 /home/user/ClaudeCode/upload_youtube.py <episode_folder_id>
```

Auto-schedules for next Wednesday 4pm UK time (minimum 2 days after upload). Sets `defaultLanguage` and `defaultAudioLanguage` to `en-GB`. Uploads thumbnail automatically if named `thumbnail` in the episode folder.

**Approval gate:**
> *"Stage 7 complete. Video scheduled for [date] at 4pm UK. Moving to Short next."*

**Do NOT declare the pipeline complete here — Stages 8 and 9 still follow.**

---

### ▶ STAGE 8 — YouTube Short

Run immediately after the main video is uploaded. Always save to Drive for Sham's approval before pushing to YouTube.

**Goal:** 55–60s vertical Short (1080×1920) with intro + key reveal + strong closing line. Scheduled for the day before the main video drops (Tuesday if main video is Wednesday).

#### Process

**Step 1 — Select three segments from `audio_timings_new.csv`:**
| Segment | What to pick | Target length |
|---|---|---|
| **Hook** | Opening scenes — establishes the two characters/comparison | ~13s |
| **Reveal** | Key numbers/conclusion — the payoff the whole video builds to | ~19–22s |
| **Closure** | A complete sentence that ends the Short naturally — check `narration_excerpt` column to find a sentence that ends with a full stop, not mid-phrase | ~21–23s |

**Critical rule — closure must end on a complete sentence.** Scan the `end_seconds` values near the target endpoint and pick the one whose `narration_excerpt` ends the thought. Never cut mid-sentence.

**Step 2 — Build and upload the Short using `create_short.py`:**

```bash
python3 /home/user/ClaudeCode/create_short.py <folder_id> <yt_video_id> "<episode_title>" "<short_title>" --schedule YYYY-MM-DDTHH:MM:SSZ
```

- `create_short.py` auto-picks hook/reveal/closure segments from `audio_timings_new.csv`
- Applies blur-background treatment automatically (16:9 source → 9:16 vertical with blurred bg)
- Schedule for the day before the main video (Tuesday 4pm BST if main is Wednesday)
- Script saves `short_preview_v1.mp4` to Drive and shares the link before pushing to YouTube

**Step 3 — Review, then upload to YouTube:**
- **Title:** Curiosity-gap hook, emoji, `#Shorts` — under 60 chars
- **Description:** One teaser line + link to full video + `Subscribe: https://www.youtube.com/@MonkeySeeMoney` + relevant hashtags
- **Pinned comment:** Link to full video, posted immediately after upload. Pin manually in Studio within 60 min of going live.

**Approval gate (preview only):**
> *"Short saved to Drive — [link]. 55s. Hook: [X]s / Reveal: [X]s / Closure: [X]s. Happy with this or want me to adjust any segment?"*

Wait for Sham's go-ahead on the preview before uploading to YouTube. Once uploaded, move immediately to Stage 9 — no further gate.

---

---

### ▶ STAGE 9 — Wrap Up (runs immediately after Stage 8 — no approval gate)

Once the Short is uploaded to YouTube:

Move the episode Drive folder into the Completed folder:

```python
requests.patch(
    f"https://www.googleapis.com/drive/v3/files/{episode_folder_id}",
    params={"addParents": "1cDd34RWgXFKzpLZ--d5JfUIocu5pZJGR", "removeParents": "1N0fFEokv69CVVMbSFbIi_FFDsab3kadR"},
    headers={"Authorization": f"Bearer {drive_token}", "Content-Type": "application/json"},
)
```

**Pipeline complete:**
> *"Pipeline complete. Video scheduled [date], Short scheduled [date-1], community post ready in 06-seo-metadata.txt — post in Studio → Community on Wednesday when the video goes live. Episode folder moved to Completed. ✓"*

---

### ▶ STAGE 10 — Analytics Review (7–14 days after publish)

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

Save a brief `09-analytics-review.md` to the episode Drive folder with:

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
| **Monkey See Money (default)** | `1N0fFEokv69CVVMbSFbIi_FFDsab3kadR` |
| Monkey Finance (old) | `1Z-aB7dKK9T9EpndozU-6lAvbxdo6yknS` |

---

## Shortcut Entry Points

| What Sham says | Start at |
|---|---|
| "Run the pipeline" / "Make a video" | Stage 1 (or Stage 2 if topic given) |
| "I have a brief, write the script" | Stage 2 |
| "Script's done, make the image prompts" | Stage 3 |
| "Generate the audio" | Stage 4 |
| "Build the video" | Stage 5 |
| "Generate the SEO" | Stage 5a |
| "Upload the video" | Stage 7 |
| "Make a Short" / "Create a Short" | Stage 8 |
| "Check the analytics" / "How did it do?" | Stage 10 (Analytics) |

---

*Individual skill docs: `monkey-finance-trends` · `monkey-finance-scriptwriter` · `monkey-finance-image-prompts` · `monkey-finance-seo-thumbnail` · `monkey-finance-tts` · `monkey-finance-video-creator`*
