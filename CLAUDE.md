# Claude Code — Project Instructions

## Fix the Root Cause First — Non-Negotiable

**Always try hard to fix the actual problem before reaching for any workaround, fallback, or alternative tool.** This is the top priority rule — it overrides convenience.

- **Never accept "it's broken" at face value.** When a command fails, investigate the real cause before doing anything else. For apt failures, run `apt-cache policy <pkg>` to check for alternate versions; for a 404 on one version, pin to a working one (e.g. `apt-get install libcaca0=0.99.beta20-4build2`). For Python errors, read the traceback and patch the actual line.
- **Fallbacks are a last resort, not a first move.** Whisper/proportional alignment, Python ffmpeg substitutes, etc. are only acceptable AFTER a genuine attempt to fix the primary tool has failed. The correct tool (e.g. aeneas for forced alignment) must always be the goal.
- **Don't blindly trust a prior "broken" note in this file.** Learnings can become stale. If a note says something is unfixable, re-investigate before accepting it — the earlier session may have given up too soon.
- **A workaround that produces lower-quality output is a failure, not a success.** Proportional timing instead of true forced alignment is worse output. Surface the trade-off explicitly and fix the real tool instead.
- **If genuinely blocked after real effort, say so clearly** — explain exactly what was tried, what the blocker is, and what's needed to unblock. Don't silently downgrade.

---

## Proactive Improvement — Non-Negotiable

These rules apply on every task, every session, without being asked:

- **End-of-stage review**: After every completed pipeline stage, before moving on, flag anything that could be better. Don't just confirm it's done — give an opinion.
- **Pipeline sequencing**: If a completed stage produces data that would improve a later stage, say so immediately. Example: Whisper timings ready → flag that SEO chapters and SRT should use them before upload.
- **Continuous improvement**: Every video should be better than the last. After each full episode is published, note what could be improved — SEO, scene pacing, image quality, caption accuracy — and carry those lessons forward.
- **Spot problems before they happen**: If a skill file, script, or process has a rule that's easy to miss or a step that's fragile, raise it proactively. Don't wait for a failed output to prove the point.
- **Never wait to be asked**: If something is suboptimal, say so. Sham should not have to find the gaps — that is my job as the expert in this pipeline.
- **Self-review before handoff**: Always review scripts and pipeline outputs for sense, flow, and formatting issues before presenting to Sham. Check for: broken callbacks (stats referenced but never introduced), wrong-direction merges, inconsistent scene structure, and content errors. Sham reviews for taste and direction — not for technical correctness.

---

## Token Efficiency — Always Apply

Be conservative with context usage on every task:

- **Skills**: Only invoke a skill when actually executing a full pipeline stage. Never invoke a skill just to answer an informational question about it.
- **File reads**: Read only the specific section or file needed. Use `grep` to find the relevant lines before committing to a full file read.
- **Reference files**: Do not load all reference files by default. Read only the one that contains what is needed for the immediate task.
- **Script runs**: Only run scripts when the user explicitly asks to build or generate something.
- **Simple requests**: Answer directly from context or a single targeted lookup — no multi-file loading for straightforward questions.
- **Parallel tool calls**: Always batch independent tool calls in a single message — never run sequentially what can run in parallel.
- **Drive searches**: Use known folder IDs directly (see below) instead of searching by name every time.
- **Specific Drive queries**: Add `mimeType` and `title contains` filters to avoid large result sets getting truncated.
- **Script output**: Pipe verbose script output through `grep -E` to show only key lines (errors, ✓ lines, totals) when full output isn't needed.
- **Trust success**: Don't re-read or re-verify files after a successful write/upload — trust the tool confirmation.
- **Git**: Always batch `git add + commit + push` into a single `&&` command, not three separate calls.
- **Avoid re-running**: If a script succeeded, don't re-run it to verify — read the printed output instead.
- **No mid-task summaries**: Don't summarise what was just done before doing the next thing — just do the next thing.

## Session Learnings Log

Add a bullet here after each session with any new pattern, bug, or convention discovered. This builds a permanent knowledge base.

- **UTF-8 decoding**: All Drive text/CSV downloads must use `r.content.decode('utf-8')` — `r.text` silently corrupts em-dashes and £ signs (latin-1 default).
- **Scene splitting**: Narration script scenes are separated by blank lines — never split by word count or sentence count.
- **Whisper alignment**: Use end-word boundary method (last 6 words of scene → `word["end"]`). Add `validate_and_fix_timings()` pass after alignment to catch speech-rate outliers (flag if duration < 0.4× or > 2.5× expected at the video's measured wpm).
- **KB every-4th**: `i > 0 and i % 4 == 1` in the render loop = 25% KB, skipping scene 0 (the opening hook). Never apply KB to the first scene.
- **SEO file format**: `06-seo-metadata.txt` must use `TITLES` as the section name (not `TITLE VARIANTS`), with `Primary:` on its own line and the title on the next line. The parser (`upload_youtube.py`) looks for `sections.get('TITLES')` and regex `PRIMARY[^\n]*\n([^\n\[]+)`. Wrong format = upload failure.
- **YouTube API**: Must be enabled in Google Cloud Console before first upload (project 452685133802). YouTube uses a separate refresh token (`youtube_refresh_token`) from Drive.
- **Audio subfolder**: For the S&P 500 war episode, audio is in an `Audio` subfolder as `.wav`, not `narration.mp3` in the root.
- **File location default**: All assets (images, audio, scripts, CSVs, videos) are always in Google Drive. Never assume local. Never search locally first. Always go to Drive.
- **Drive folder ID verification**: At the start of any new session that involves saving pipeline files, always confirm the episode folder ID via a Drive search before saving anything. Never trust a cached ID in CLAUDE.md without verification. After creating or finding the correct folder, update CLAUDE.md immediately.
- **No SRT generation**: YouTube auto-generates captions. Never run generate_srt.py. Set `defaultLanguage` and `defaultAudioLanguage` to `en-GB` on upload — that's all that's needed.
- **Pinned comment**: upload_youtube.py auto-posts the pinned comment after upload. BUT it only works on public/unlisted videos — not private/scheduled. For scheduled videos, post the comment manually in Studio once live, then pin it (3 dots → Pin) within 60 min.
- **Auto-scheduling**: upload_youtube.py automatically schedules publish for next Wednesday at 4pm UK time, minimum 2 days after upload. No `--privacy` flag needed — scheduling is always on.
- **Filename = title slug**: Video and thumbnail filenames must match the video title (slugified). This is SEO best practice. upload_youtube.py handles this automatically.
- **Thumbnail in Drive**: Name the thumbnail file "thumbnail" in the episode folder. upload_youtube.py will find it and upload it automatically alongside the video.
- **KB movement file**: Old `05-kb-movements.txt` has verbose descriptions — `movement_to_effect_idx()` should return `None` for unrecognised text and fall back to cycling, not default to pan left to right.
- **KB sample image**: Use file ID `17FRRCFFkVRQUuSC8t7fsPEmjSEgzd88p` from the S&P 500 vs Stocks episode for future KB sample generation.
- **YouTube Brand Account**: Monkey See Money is a Brand Account on the same Google email as Digital Fusion. Always run `setup_youtube_auth.py` and select **Monkey See Money** — not the personal/Digital Fusion account. The wrong channel auth will silently upload to the wrong channel.
- **Pre-upload channel check — mandatory**: Before every `upload_youtube.py` run, verify the authenticated channel via `GET /youtube/v3/channels?part=snippet&mine=true`. Confirm it returns "Monkey See Money" before proceeding. If it returns anything else, stop and re-authenticate.
- **Skip-a-Wednesday scheduling**: To target the Wednesday after next, temporarily set `MIN_DAYS_BUFFER = 4` in `upload_youtube.py` before running, then reset to `2` immediately after. With buffer=4, today (Mon) + 4 days = Fri, next Wednesday = the one after next.
- **YouTube auth scope**: `setup_youtube_auth.py` now requests both `youtube` and `youtube.force-ssl` scopes — the force-ssl scope is required for posting comments. If comment posting returns 403, re-run auth.
- **upload_youtube.py rename bug**: The slug rename must happen AFTER download, not before. File is downloaded directly to the slugged filename path now — do not reintroduce a pre-download rename.
- **Thumbnail mime type**: Thumbnails may be PNG not JPEG. upload_youtube.py now reads the actual Drive mimeType and sends the correct Content-Type header. Do not hardcode `image/jpeg`.
- **AI video clips pipeline**: `create_video_from_clips.py` replaces `create_video_kb.py` when using AI-generated video clips instead of KB-effect images. Looks for `Videos` subfolder, `audio_timings_new.csv`, and audio file. Slows clips where scene > clip duration, trims where scene < clip duration.
- **Monkey action rule**: Every monkey scene must show the monkey mid-action with a prop (pressing button, holding umbrella, looking through binoculars, etc.). Never just standing. Enforced in VISUAL-RULES.md and SKILL.md.
- **aeneas forced alignment**: replaces Whisper-based matching in `generate_timings_whisper.py`. Install: `apt-get install -y libespeak-dev` then `pip install setuptools==65.5.0 && python setup.py install` from extracted aeneas-1.7.3.0 source, then `pip install --upgrade setuptools`. Requires patching `wavfile.py` to replace `numpy.fromstring` with `numpy.frombuffer`. Takes 16kHz mono WAV — script converts MP3 automatically via ffmpeg. Duration range 1.48s–14.24s, zero suspects, no post-processing needed.
- **YouTube transcript extraction**: yt-dlp and youtube-transcript-api both get 403 from this server's IP — YouTube blocks it. Use Gemini API instead: `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}` with `{"file_data": {"mime_type": "video/*", "file_uri": "https://www.youtube.com/watch?v=VIDEO_ID"}}` as a part alongside the text prompt. Gemini natively reads YouTube URLs and returns full transcripts. Use model `gemini-2.5-flash` — `gemini-2.0-flash` may hit quota limits.
- **Competitor video research**: To find a competitor video ID, use the YouTube Data API search endpoint with a refreshed `youtube_refresh_token`: `GET https://www.googleapis.com/youtube/v3/search?part=snippet&q=QUERY&type=video` with Bearer auth. Then pass the video ID to Gemini for transcript extraction.
- **Script style — character-driven**: Scripts perform better with named characters (e.g. Jake and Marcus) rather than abstract "you vs you" comparisons. The Wealth Logic "Real Estate vs Stocks" format (1.48M views) uses two characters to make the emotional journey concrete and followable. Adopt this structure for comparison videos.
- **Character names rotate every episode**: Never reuse the same character names across episodes. Suggested pairs: Jake/Marcus, Sarah/David, Emma/Tom, Priya/James, Sophie/Chris, Aisha/Ben.
- **Character reference file**: For every episode with named characters, create `00b-character-references.txt` in the episode Drive folder immediately after the script is approved. Include: one Grok image prompt per character (full reference sheet with 4 poses), colour identity, signature prop, scenes they appear in, and usage notes. File named `00b-` so it sorts near the top. Characters are 2D whiteboard animation style — NOT photorealistic.
- **Script adaptation workflow**: Find the top-performing competitor video on a topic → extract transcript via Gemini → adapt to UK (swap $ for £, add ISA/CGT/Section 24/stamp duty, change characters/scenarios) → keep the proven emotional beats and structure intact.
- **Script file word counts**: Always include word count in the metadata header of `02-narration-script-structured.txt` AND in the filename/header of the source transcript file (e.g. `00-source-transcript-[channel]-original.txt`). Format: `# Word count: X words` in the header block.
- **Source transcript filing**: Always save the original competitor transcript to Drive as `00-source-transcript-[channel-name]-original.txt` in the episode folder immediately after extraction. Prefix `00-` so it sorts to the top as a reference file.
- **TTS daily quota**: `gemini-2.5-flash-preview-tts` free tier hits a daily quota after ~13 chunks (~150 words each, ~2,000 words total). Chunks are saved locally to `/home/user/ClaudeCode/tts_chunks/` and the script resumes automatically on re-run — only missing chunks are regenerated. If quota is hit, wait until the next day (resets ~midnight Pacific / ~8am UK) and re-run. Do NOT delete chunk files between sessions. **TTS uses `gemini_tts_api_key` from token.json** (separate paid key) — falling back to `gemini_api_key` only if not set.
- **ALWAYS use aeneas for timings — NON-NEGOTIABLE**: Forced alignment via aeneas is mandatory for every episode. Proportional and Whisper fallbacks are BANNED for final output — they drifted up to 6 seconds vs aeneas on real measurement (e.g. Diane's chapter −6s, takeaways +6s). If aeneas fails, FIX the environment (libcaca0 pin + libespeak-dev + wavfile.py frombuffer patch) — do NOT downgrade to a fallback. A non-aeneas CSV is unacceptable output. If aeneas genuinely cannot run after real effort, stop and report it — never silently ship proportional/Whisper timings.
- **Pipeline stage order (updated)**: After TTS, run aeneas timings (`generate_timings.py`) → then SEO. Video assembly (create_video_kb.py) runs separately after images are generated. Do NOT block SEO on video assembly — SEO only needs `audio_timings_new.csv` for chapter timestamps.
- **aeneas environment setup — full fix sequence**: On a fresh host, set up aeneas with these exact steps (all required, in order): (1) `apt-get install -y libcaca0=0.99.beta20-4build2` — the security update `0.99.beta20-4ubuntu0.1` 404s, so pin to the stable noble/main version; this also unblocks ffmpeg/ffprobe. (2) `apt-get install -y libespeak-dev`. (3) `pip install aeneas`. (4) Patch `numpy.fromstring` → `numpy.frombuffer` on line ~78 of `/usr/local/lib/python3.11/dist-packages/aeneas/wavfile.py` (numpy 2.x removed `fromstring`; without this aeneas throws `AudioFileUnsupportedFormatError`). Verify with `python3 -c "from aeneas.executetask import ExecuteTask; print('ok')"`. Run this whole sequence up front in any session that will generate timings.
- **Whisper fallback (BANNED for final output)**: Whisper proportional alignment exists in `generate_timings.py` only as an emergency last resort. It is NOT to be used for shipped videos — see the aeneas non-negotiable rule above. Fix aeneas instead.
- **Google OAuth 7-day expiry**: Drive refresh tokens expire every 7 days when the Google Cloud app is in **Testing** mode. Fix once and permanently: Google Cloud Console → APIs & Services → OAuth consent screen → Publish App. After publishing, run `python3 setup_auth.py` one final time — the new refresh token will never expire.
- **Karaoke subtitles — use PIL not ASS**: ASS `\bord` trick creates a rounded bubble/glow effect, not a clean rectangle. Use PIL (`Pillow`) to render subtitle frames as RGBA PNGs with `draw.rounded_rectangle()` for the green box, then composite as a MOV overlay using `ffmpeg overlay` filter. Font: `LiberationSans-Bold.ttf` at `/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf`.
- **PIL subtitle box positioning**: Use raw `font.getbbox()` values — `bb[1]` = glyph top offset, `bb[3]` = glyph bottom offset from the draw coordinate. Box y1 = `y_text + bb[1] - BOX_PAD_V`, box y2 = `y_text + bb[3] + BOX_PAD_V`. Anchor `y_text = h - SUB_MARGIN_V - max(bb[3])` so the glyph bottom sits at the margin. Never use `bb[3] - bb[1]` for the box bottom — that subtracts the top offset twice and clips the text.
- **Subtitle settings (confirmed working)**: FONT_SIZE=64, PHRASE_LEN=4 words, BOX_PAD_H=18, BOX_PAD_V=10, BOX_RADIUS=8, SUB_MARGIN_V=90. Green colour `(0, 200, 0, 255)`. White text with black stroke_width=2.
- **`create_sample.py`**: New script for 30-second preview renders. Flags: `--crossfade` (0.3s dissolve between scenes), `--output=filename.mp4`. Picks scenes from the start of the episode up to ~30s. Use this before committing to a full render to validate KB motion, subtitle style, and transitions.
- **Preferred transition**: Crossfade 0.3s dissolve (`--crossfade`) is the preferred style — smoother than hard cuts without slowing the pace. Hard cuts are the fallback if render time is a concern.
- **generate_timings.py rename bug**: The git rename commit (`eae9490`) deleted the aeneas version and left the old proportional code in place because `generate_timings.py` already existed. Always verify file content after a git rename — don't trust the commit message alone.
- **Shorts — mandatory after every upload**: Every long-form video must have a companion Short. Run `create_short.py` after `upload_youtube.py` for every episode. Schedule the Short for the day after the main video uploads (Thursday if main is Wednesday at 4pm). Script auto-picks hook/reveal/closure from `audio_timings_new.csv`; falls back to proportional if no CSV. Always validate Short duration is 54–62s before uploading to YouTube. The closure extension loop must cap at `closure_start + closure_target + 5s` — never grow the window dynamically.
- **Shorts segment validation**: Before building a Short, always ffprobe the source MP4 duration and cap all segment endpoints to `actual_duration - 0.5s`. If CSV end_seconds > 1.5× video duration, the CSV belongs to a different episode — discard and use proportional timing.

## Known Drive Folder IDs

| Location | Folder ID |
|---|---|
| **Monkey See Money (default root)** | `1N0fFEokv69CVVMbSFbIi_FFDsab3kadR` |
| Monkey Finance (old root) | `1Z-aB7dKK9T9EpndozU-6lAvbxdo6yknS` |
| S&P 500 vs Picking Your Own Stocks (53 scenes) | `1VSu4FuGUQhDxk6yC5HAjnze6YetAEecO` |
| S&P 500 All-Time High During War (51 scenes) | `1fFJnQTbnJ6hAKmD5sXDhVFdk77U_f52U` |
| The Savings Tax Trap | `1lfFqd3FuqEXJx5DNMKP1YqnXTK1_W2dc` |
| Car Finance — Leasing vs Buying: The Real Math (UK) | `1MFf07I2leM6_iyvB5bGXNyqRgYhv35SI` |
| Psychology of Gen X Money Habits UK | `1ziC-h6dbPrRtaGFUXS43lzIz4m_gpzrN` |
| The One Financial Mistake Every Generation Repeats (UK) | `1JemV1boJxO_IIDDw5cGfcj5txp8jICzI` |
| Completed episodes (archive) | `1cDd34RWgXFKzpLZ--d5JfUIocu5pZJGR` |
| 10 Bad Money Habits | `1r4Ay0qa-Z8eBSioyXlwurUd_rt839EZj` |
| Property vs Stocks — The Real Math | `14wJDYLxkPX2_ltbwxv8VS8b2kk4orMVq` |

## Project Overview

Monkey Finance — automated YouTube video production pipeline.

### Key Scripts
| Script | Purpose |
|---|---|
| `generate_timings.py` | aeneas forced alignment → `audio_timings_new.csv` (requires libespeak-dev + ffmpeg) |
| `create_video_kb.py` | Assembles images + audio into MP4 with Ken Burns effects |
| `upload_youtube.py` | Uploads finished video to YouTube with SEO metadata |
| `setup_youtube_auth.py` | One-time YouTube OAuth setup |
| `run_tts.py` | Text-to-speech narration generation |
| `create_short.py` | Build + upload YouTube Short from episode folder. Args: `<folder_id> <yt_video_id> "<episode_title>" "<short_title>" --schedule YYYY-MM-DDTHH:MM:SSZ` |

### Key Conventions
- All secrets in `token.json` (gitignored) — never hardcode keys
- Audio/text files from Drive always decoded as UTF-8 (`r.content.decode('utf-8')`)
- Scene splits by blank line in narration script (one paragraph = one scene)
- KB effects: 25% of scenes (every 4th); cosine ease-in/out on all effects; zoom-in skipped on scenes >8s (swaps to pan bottom→top)
- Image prompts: 20% border instruction goes SECOND in the prompt (immediately after "2D colourful whiteboard animation style. Clean white background."); never specify monkey suit colour
- Development branch: `claude/general-session-8o65N`
- Whisper model: base (139MB at `~/.cache/whisper/base.pt`)
