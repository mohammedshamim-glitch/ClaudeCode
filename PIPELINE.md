# Monkey See Money — Video Production Pipeline

Full process from topic idea to published YouTube video + Short.

---

## Quick Reference

| What you need | Where to find it |
|---|---|
| Drive root folder | `1N0fFEokv69CVVMbSFbIi_FFDsab3kadR` |
| Completed episodes | `1cDd34RWgXFKzpLZ--d5JfUIocu5pZJGR` |
| All secrets | `token.json` (local, gitignored) |
| YouTube channel | Monkey See Money (Brand Account) |

---

## Stage Overview

| # | Stage | Output files |
|---|---|---|
| 1 | Trend research | `01-trend-report.md` |
| 2 | Script writing | `02-narration-script-structured.txt` + `03-narration-script-clean.txt` |
| 3 | Image prompts | `04-image-prompts.txt` + `05-video-prompts.txt` |
| 4 | TTS audio | `narration.mp3` |
| 5 | Timing alignment | `audio_timings_new.csv` |
| 6 | SEO & thumbnail | `06-seo-metadata.txt` + `07-thumbnail-prompt.txt` |
| 7 | Video assembly | `<episode-title>.mp4` |
| 8 | YouTube upload | Published/scheduled video |
| 9 | YouTube Short | `short_preview_v1.mp4` → YouTube Short |

---

## Stage 1 — Trend Research

**Goal:** Find the best topic for the next video.

Run Claude Code and invoke `/monkey-finance-trends` — it will:
- Pull live data from competitor channels via yt-dlp
- Search for trending and evergreen finance topics
- Score each opportunity and recommend the top pick

**Output:** `01-trend-report.md` saved to the episode Drive folder.

**Approval gate:** Confirm the topic before moving to Stage 2.

---

## Stage 2 — Script Writing

**Goal:** Write the full narration script (~2,000 words, 25-word scenes).

Invoke `/monkey-finance-scriptwriter` with the approved topic and content brief.

The scriptwriter will:
- Write a 1,900–2,100 word narration using the 4-pass method
- Break it into 25-word scenes (min 20, max 35 words per scene)
- Save the structured script as `02-narration-script-structured.txt`
- Save the clean TTS-ready script as `03-narration-script-clean.txt`

**Approval gate:** Review the script. Request any edits before proceeding.

> **Note:** For comparison/character episodes, create `00b-character-references.txt` immediately after script approval — one image prompt per character (4-pose reference sheet), colour identity, signature prop, scenes they appear in.

---

## Stage 3 — Image Prompts

**Goal:** Generate one image prompt and one video prompt per narration scene.

Invoke `/monkey-finance-image-prompts` pointing at the clean narration script.

Rules:
- One prompt per scene — no merging, no grouping
- Every prompt: `2D colourful whiteboard animation style. Clean white background. All critical elements within the central 60% of the frame — minimum 20% clear margin on all edges. 16:9 widescreen aspect ratio, landscape composition.`
- Monkey in ~25% of scenes — always mid-action with a prop, never just standing
- Never specify suit colour
- Every stat/number must be drawn on the canvas in the prompt
- Named characters must appear in scenes that reference them

**Output:** `04-image-prompts.txt` + `05-video-prompts.txt` saved to Drive.

**Approval gate:** Review prompts before generating images.

---

## Stage 4 — Audio Generation (TTS)

**Goal:** Generate the narration audio from the clean script.

```bash
python3 /home/user/ClaudeCode/run_tts.py <narration_file_id> <episode_folder_id> narration.mp3
```

- Uses `gemini_tts_api_key` from `token.json` (separate from main Gemini key)
- Chunks are cached locally in `tts_chunks/` — re-run is safe if quota is hit
- Free tier quota: ~2,000 words/day — resets ~8am UK time
- Output: `narration.mp3` uploaded to Drive

**Approval gate:** Confirm audio sounds correct before timing generation.

---

## Stage 5 — Timing Alignment (aeneas)

**Goal:** Generate precise word-level timestamps for each narration scene.

```bash
python3 /home/user/ClaudeCode/generate_timings.py <episode_folder_id>
```

**Critical:** This MUST use aeneas forced alignment. Proportional and Whisper fallbacks are banned for final output — they drift up to 6 seconds vs aeneas.

**Environment setup (if aeneas not yet installed):**
```bash
apt-get install -y libcaca0=0.99.beta20-4build2
apt-get install -y libespeak-dev
pip install aeneas
# Patch numpy: edit /usr/local/lib/python3.11/dist-packages/aeneas/wavfile.py
# Line ~78: numpy.fromstring → numpy.frombuffer
```

**Output:** `audio_timings_new.csv` uploaded to Drive.

---

## Stage 6 — SEO & Thumbnail

**Goal:** Create the complete click package: titles, description, tags, chapters, thumbnail brief.

Invoke `/monkey-finance-seo-thumbnail` — it will:
- Engineer 3 title variants (primary + 2 A/B tests)
- Write the 300–500 word description (front-loaded, keyword-rich)
- Generate tags (10–12), hashtags (3–5), and chapters from `audio_timings_new.csv`
- Produce a thumbnail brief and Grok image generation prompt

**Output:**
- `06-seo-metadata.txt` — full SEO package
- `07-thumbnail-prompt.txt` — raw Grok prompt (paste directly into Grok)

**Before upload:** Save the generated thumbnail to Drive named exactly `thumbnail` — `upload_youtube.py` finds it by that name automatically.

**Approval gate:** Review title variants and thumbnail before upload.

---

## Stage 7 — Video Assembly

**Goal:** Assemble images + audio into the final MP4.

Images must be in Drive under an `Images` subfolder, numbered sequentially (1, 2, 3... matching narration scenes).

```bash
python3 /home/user/ClaudeCode/create_video_kb.py <episode_folder_id>
```

This applies Ken Burns effects (zoom/pan) to every 4th scene (25% of scenes), with crossfade transitions between scenes.

**Output:** `<episode-title>.mp4` uploaded to Drive.

> **Verify before running:** Confirm image count = scene count. If images have section-based numbering (e.g. 110, 210, 211) instead of sequential numbering, they must be renamed first or the video will be out of sync with the narration.

---

## Stage 8 — YouTube Upload

**Pre-upload channel check — mandatory every time:**
```bash
# Verify you're uploading to Monkey See Money, not another channel
# upload_youtube.py does this check automatically
```

```bash
python3 /home/user/ClaudeCode/upload_youtube.py <episode_folder_id>
```

This will:
- Parse `06-seo-metadata.txt` for title, description, tags, chapters
- Upload the MP4 via resumable upload
- Upload the `thumbnail` file from Drive
- Schedule publish for **next Wednesday at 4pm UK time** (minimum 2 days buffer)
- Set `defaultLanguage` and `defaultAudioLanguage` to `en-GB` (auto-captions)
- Print the YouTube video URL

**After upload:**
- Move the episode folder to Completed: parent → `1cDd34RWgXFKzpLZ--d5JfUIocu5pZJGR`
- Note the YouTube video ID for the Short

---

## Stage 9 — YouTube Short

**Goal:** Create a 55–60s vertical Short from the best moments of the episode.

```bash
python3 /home/user/ClaudeCode/create_short.py \
  <episode_folder_id> \
  <youtube_video_id> \
  "<Episode Title>" \
  "<Short Title>" \
  --schedule YYYY-MM-DDTHH:MM:SSZ
```

The script auto-selects three segments from `audio_timings_new.csv`:
- **Hook** (~13s) — opening scenes
- **Reveal** (~19–22s) — the key payoff moment
- **Closure** (~21–23s) — a complete sentence that ends naturally

Schedule the Short for **Tuesday at 4pm** (the day before the main video).

**After upload — manual actions required:**
1. **Pin comment** once live: `"Full video here 👉 https://www.youtube.com/watch?v=<VIDEO_ID>"`
2. **Set Related Video** in Studio → Edit Short → Customisation → Related video → link to full video

---

## Post-Publication Checklist

- [ ] Pin comment on the Short (within 60 min of going live)
- [ ] Set Related Video on the Short in Studio
- [ ] Episode folder moved to Completed in Drive
- [ ] CLAUDE.md updated with new episode folder ID and YouTube ID

---

## 7-Day Analytics Review

Run 7 days after publish (and again at 14 days):

Invoke `/monkey-finance-trends` → analytics mode, or check YouTube Studio manually:

| Metric | Target |
|---|---|
| Impressions CTR | 4–6% solid, 6%+ excellent |
| Average view duration | 50%+ of video length |
| Top traffic source | Search or Suggested |

Key questions:
1. Did the packaging work? (CTR)
2. Did the content work? (view duration)
3. Where did traffic come from?
4. Which A/B title won?

Save findings as `08-analytics-review.md` in the episode Drive folder and feed learnings into the next trend report.

---

## Scheduling Rules

| Video type | Schedule |
|---|---|
| Main video | Wednesday at 4pm UK time |
| YouTube Short | Tuesday at 4pm UK time (day before) |
| Minimum buffer | 2 days after upload date |
| Skip-a-Wednesday | Set `MIN_DAYS_BUFFER = 4` in `upload_youtube.py` before running, reset to `2` after |

---

## Common Fixes

**TTS quota hit** — Wait until ~8am UK (resets daily). Re-run the same command — chunks are cached, only missing ones regenerate.

**aeneas install fails** — Pin libcaca0 to `0.99.beta20-4build2` (the security update 404s). Then: `apt-get install -y libespeak-dev` → `pip install aeneas` → patch `wavfile.py` (`fromstring` → `frombuffer`).

**YouTube upload "could not parse title"** — Check `06-seo-metadata.txt` uses `[TITLES]` as section header with `Primary:` on its own line. The parser requires this exact format.

**Images out of sync with audio** — Check image count equals scene count. Check images are numbered sequentially (1, 2, 3...) not section-based (1.1, 1.2 → 11, 12). Rename if needed before running `create_video_kb.py`.

**Wrong YouTube channel** — Re-run `setup_youtube_auth.py` and select **Monkey See Money** (Brand Account), not the personal/Digital Fusion account.

**Drive refresh token expired** — Tokens expire every 7 days in Testing mode. Fix permanently: Google Cloud Console → OAuth consent screen → **Publish App**. Then re-run `setup_auth.py` once.
