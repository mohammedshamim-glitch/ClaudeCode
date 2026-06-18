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
- **Pipeline sequencing**: If a completed stage produces data that would improve a later stage, say so immediately. Example: aeneas timings ready → flag that SEO chapters should use them before upload.
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
- **Episode folder naming — must include date**: All episode Drive folders must be named with a date prefix in the format `YYYY-MM-DD — [Episode Title]`, e.g. `2026-06-18 — What Happens When You Invest £500 Per Month (Year By Year)`. If a folder exists without a date, rename it immediately before saving any files.
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
- **yt-dlp SSL blocked**: yt-dlp fails on this server with SSL certificate errors (self-signed cert in chain). Use the YouTube Data API (`/youtube/v3/search` + `/youtube/v3/videos?part=snippet,statistics`) for competitor tag extraction instead. Same data, no SSL issues. Never attempt yt-dlp for YouTube — go straight to the Data API.
- **Script style — character-driven**: Scripts perform better with named characters (e.g. Jake and Marcus) rather than abstract "you vs you" comparisons. The Wealth Logic "Real Estate vs Stocks" format (1.48M views) uses two characters to make the emotional journey concrete and followable. Adopt this structure for comparison videos.
- **Fixed character roster — 5 characters, 0–3 per episode**: There are exactly 5 named characters used across all Monkey Finance episodes: Emma, Tom, Sarah, James, Aisha. Each episode uses 0, 1, 2, or 3 of them — never more than 3. Some videos have no named characters at all (monkey only). Never create new characters outside the five. Avoid reusing the exact same combination in consecutive episodes. Full appearance descriptions and standing-pose prompts are in `references/CHARACTERS.md` in the scriptwriter skill folder.
- **Character reference file**: Only create `00b-character-references.txt` if the episode has named characters. If monkey-only, skip it. When characters are used, include one one-liner standing-pose Grok prompt per character (copied from `CHARACTERS.md`), colour identity, scenes they appear in, and usage notes. File named `00b-` so it sorts near the top. Characters are 2D whiteboard animation style — NOT photorealistic. **Each character gets exactly one standing-pose prompt — no action poses, no 4-pose sheets.**
- **Script adaptation workflow**: Find the top-performing competitor video on a topic → extract transcript via Gemini → adapt to UK (swap $ for £, add ISA/CGT/Section 24/stamp duty, change characters/scenarios) → keep the proven emotional beats and structure intact.
- **Script file word counts**: Always include word count in the metadata header of `02-narration-script-structured.txt` AND in the filename/header of the source transcript file (e.g. `00-source-transcript-[channel]-original.txt`). Format: `# Word count: X words` in the header block.
- **Source transcript filing**: Always save the original competitor transcript to Drive as `00-source-transcript-[channel-name]-original.txt` in the episode folder immediately after extraction. Prefix `00-` so it sorts to the top as a reference file.
- **TTS daily quota**: `gemini-2.5-flash-preview-tts` free tier hits a daily quota after ~13 chunks (~150 words each, ~2,000 words total). Chunks are saved locally to `/home/user/ClaudeCode/tts_chunks/` and the script resumes automatically on re-run — only missing chunks are regenerated. If quota is hit, wait until the next day (resets ~midnight Pacific / ~8am UK) and re-run. Do NOT delete chunk files between sessions. **TTS uses `gemini_tts_api_key` from token.json** (separate paid key) — falling back to `gemini_api_key` only if not set.
- **ALWAYS use aeneas for timings — NON-NEGOTIABLE**: Forced alignment via aeneas is mandatory for every episode. Proportional and Whisper fallbacks are BANNED for final output — they drifted up to 6 seconds vs aeneas on real measurement (e.g. Diane's chapter −6s, takeaways +6s). If aeneas fails, FIX the environment (libcaca0 pin + libespeak-dev + wavfile.py frombuffer patch) — do NOT downgrade to a fallback. A non-aeneas CSV is unacceptable output. If aeneas genuinely cannot run after real effort, stop and report it — never silently ship proportional/Whisper timings.
- **Pipeline stage order (FIXED — non-negotiable)**: Stage 2 Script → Stage 3 Image prompts (`04-image-prompts.txt`) → Stage 4 TTS (`narration.mp3`) → Stage 5a aeneas timings + SEO (`06-seo-metadata.txt`, `07-thumbnail-prompt.txt`) → Stage 5b video assembly (`create_video_kb.py --subs`) → Stage 7 upload → Stage 8 Short → Stage 9 community post. **Approval gate after every stage — always wait for Sham's sign-off before proceeding to the next stage.** Never skip a stage. Never run stages out of order.
- **Video assembly — always use --subs flag**: `create_video_kb.py` requires `--subs` to burn karaoke word-highlight subtitles into the video. NEVER run it without `--subs`. Command: `python3 create_video_kb.py <folder_id> --subs`. Omitting `--subs` produces a video with no subtitles.
- **aeneas environment setup — full fix sequence**: On a fresh host, set up aeneas with these exact steps (all required, in order): (1) `apt-get install -y libcaca0=0.99.beta20-4build2` — the security update `0.99.beta20-4ubuntu0.1` 404s, so pin to the stable noble/main version; this also unblocks ffmpeg/ffprobe. (2) `apt-get install -y libespeak-dev`. (3) `pip install aeneas`. (4) Patch `numpy.fromstring` → `numpy.frombuffer` on line ~78 of `/usr/local/lib/python3.11/dist-packages/aeneas/wavfile.py` (numpy 2.x removed `fromstring`; without this aeneas throws `AudioFileUnsupportedFormatError`). Verify with `python3 -c "from aeneas.executetask import ExecuteTask; print('ok')"`. Run this whole sequence up front in any session that will generate timings.
- **Whisper fallback (BANNED for final output)**: Whisper proportional alignment exists in `generate_timings.py` only as an emergency last resort. It is NOT to be used for shipped videos — see the aeneas non-negotiable rule above. Fix aeneas instead.
- **Google OAuth 7-day expiry**: Drive refresh tokens expire every 7 days when the Google Cloud app is in **Testing** mode. Fix once and permanently: Google Cloud Console → APIs & Services → OAuth consent screen → Publish App. After publishing, run `python3 setup_auth.py` one final time — the new refresh token will never expire.
- **Karaoke subtitles — use PIL not ASS**: ASS `\bord` trick creates a rounded bubble/glow effect, not a clean rectangle. Use PIL (`Pillow`) to render subtitle frames as RGBA PNGs with `draw.rounded_rectangle()` for the green box, then composite as a MOV overlay using `ffmpeg overlay` filter. Font: `LiberationSans-Bold.ttf` at `/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf`.
- **PIL subtitle box positioning**: Use raw `font.getbbox()` values — `bb[1]` = glyph top offset, `bb[3]` = glyph bottom offset from the draw coordinate. Box y1 = `y_text + bb[1] - BOX_PAD_V`, box y2 = `y_text + bb[3] + BOX_PAD_V`. Anchor `y_text = h - SUB_MARGIN_V - max(bb[3])` so the glyph bottom sits at the margin. Never use `bb[3] - bb[1]` for the box bottom — that subtracts the top offset twice and clips the text.
- **Subtitle settings (confirmed working)**: FONT_SIZE=42, PHRASE_LEN=5 words, BOX_PAD_H=14, BOX_PAD_V=7, BOX_RADIUS=6, SUB_MARGIN_V=55. Green colour `(0, 200, 0, 255)`. White text with black stroke_width=2. ALL CAPS. Active word gets green box, rest plain white.
- **`create_sample.py`**: New script for 30-second preview renders. Flags: `--crossfade` (0.3s dissolve between scenes), `--output=filename.mp4`. Picks scenes from the start of the episode up to ~30s. Use this before committing to a full render to validate KB motion, subtitle style, and transitions.
- **Preferred transition**: Crossfade 0.3s dissolve (`--crossfade`) is the preferred style — smoother than hard cuts without slowing the pace. Hard cuts are the fallback if render time is a concern.
- **generate_timings.py rename bug**: The git rename commit (`eae9490`) deleted the aeneas version and left the old proportional code in place because `generate_timings.py` already existed. Always verify file content after a git rename — don't trust the commit message alone.
- **Shorts — mandatory after every upload**: Every long-form video must have a companion Short. Run `create_short.py` after `upload_youtube.py` for every episode. Schedule the Short for the day **before** the main video goes live (Tuesday if main is Wednesday at 4pm). Script auto-picks hook/reveal/closure from `audio_timings_new.csv`; falls back to proportional if no CSV. Duration target is flexible — what matters is that the Short makes sense as a standalone clip. The closure extension loop must cap at `closure_start + closure_target + 5s` — never grow the window dynamically.
- **Shorts segment validation**: Before building a Short, always ffprobe the source MP4 duration and cap all segment endpoints to `actual_duration - 0.5s`. If CSV end_seconds > 1.5× video duration, the CSV belongs to a different episode — discard and use proportional timing.
- **Scene format (Wealth Logic style) — correct pattern**: One visual beat = one scene. Word count varies 5–29 words — there is NO fixed target. Short consecutive sentences that share the same visual moment may be grouped. Sham edits scene boundaries directly in the V2 Google Doc; Claude reverse-engineers the structured script and image prompts to match exactly. Never impose a word-count boundary that breaks a visual moment.
- **Image prompts only — video prompts file deprecated**: `05-video-prompts.txt` is no longer generated. Stage 3 produces only `04-image-prompts.txt`. Do not generate, save, or reference `05-video-prompts.txt` going forward.
- **Monkey article rule**: Always write "Monkey" not "A monkey" in image prompts. Never use the indefinite article before monkey.
- **No celebrity names in image prompts — non-negotiable**: Never mention any real person's name (celebrity, politician, CEO, public figure) in any image prompt or scene description. Reference the role/concept instead (e.g. "a tech billionaire", "a rocket launch", "a company founder"). AI image generators will reject prompts containing real names and block scene generation.
- **Character appearance rule**: In **scene image prompts** (`04-image-prompts.txt`) — never describe clothing, hair, or physical appearance. Only describe action, props, and facial expression. In **character reference one-liners** (`00b-character-references.txt`) — appearance IS described, because that is specifically where visual identity is established. The distinction: reference file defines the look once; scene prompts use the character by name and action only.
- **Character facial expressions — mandatory**: Every named character scene must specify a contextually appropriate facial expression. Match the emotion of the narration: anxious/worried for bad scenarios, confident/relieved for wins, surprised/concerned for reveals, thoughtful/pleased for realisations. A scene with a named character and no expression note is a failed prompt.
- **Drive uploads — use Python requests, not MCP tool**: `mcp__99a10a78__create_file` / `update_file` tools frequently hit approval-prompt loops and fail silently. Always upload/update Drive files using `requests` with Drive API v3 directly (Bearer token from `drive_refresh_token`). See the multipart upload pattern in the session learnings above.
- **Google Doc export BOM**: When exporting a Google Doc as plain text (`export?mimeType=text/plain`), strip the UTF-8 BOM with `.lstrip('﻿')` after `.decode('utf-8')`. Without this, scene-splitting logic fails on the first scene.
- **Flash TTS pace variance — pace-lock is mandatory**: Without intervention, Flash chunks range 145–195 wpm (a 50 wpm swing), producing audibly inconsistent audio. `run_tts.py` now includes a `pace_lock()` pass that measures each chunk's wpm and applies `ffmpeg atempo` (pitch-preserving tempo stretch) to normalise all chunks to the median wpm before merging. This is automatic — do not remove it.
- **Flash speaks any text prefix aloud**: Flash cannot follow instructions embedded in the prompt text — it will voice them as narration. `PACE_INSTRUCTION` in `run_tts.py` is therefore Pro-only (gated by `"pro" in TTS_MODEL`). Flash's pace consistency relies entirely on balanced chunking + pace-lock, not on instruction prefixes.
- **Re-run aeneas after every TTS regeneration**: Any time `run_tts.py` produces a new `narration.mp3`, aeneas MUST be re-run (`python3 generate_timings.py <folder_id>`) before video assembly. The old `audio_timings_new.csv` will be misaligned with the new audio length — never reuse it.
- **Competitor transcript is MANDATORY before scripting — NON-NEGOTIABLE**: Before writing a single word of any script, find the top-performing Wealth Logic video on the topic and download its transcript via Gemini API (use `gemini_tts_api_key` — NOT `gemini_api_key`, which hits free-tier quota). Save immediately as `00-source-transcript-wealth-logic-original.txt` in the episode Drive folder. Then adapt from that transcript — never write from scratch when a Wealth Logic video on the topic exists. Skipping this step and writing original scripts is a process failure. The script adaptation workflow (Competitor Adaptation Workflow in the scriptwriter skill) is mandatory, not optional.

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
| The One Financial Mistake Every Generation Repeats (UK) | `1JemV1boJxO_IIDDw5cGfcj5txp8jICzI` | YT: `Xg-m1V6I5sE` |
| Completed episodes (archive) | `1cDd34RWgXFKzpLZ--d5JfUIocu5pZJGR` |
| 10 Bad Money Habits | `1r4Ay0qa-Z8eBSioyXlwurUd_rt839EZj` |
| Property vs Stocks — The Real Math | `14wJDYLxkPX2_ltbwxv8VS8b2kk4orMVq` |
| ISA vs Pension — Which One Will Make You More Money? (The Real Math) | `1E_dBFxc1Cn0XtqiVS4bu6k2oiEwtWZwb` |
| SpaceX Just Went Public — And The Real Risk Starts Now | `13qgKco77jUIlKQPl-r8YViV5SctqR0U1` |
| 2026-06-18 — What Happens When You Invest £500 Per Month (Year By Year) | `1EnDHYa0_U6NPh2vy9mai20Nj_fBh-gsM` |

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
- KB effects: 25% of scenes (every 4th); cosine ease-in/out on all effects; 4 effects cycle: pan left→right, pan right→left, pan top→bottom, pan bottom→top
- Image prompts: 20% border instruction goes SECOND in the prompt (immediately after "2D colourful whiteboard animation style. Clean white background."); never specify monkey suit colour
- Development branch: `claude/general-session-8o65N`
- Timing method: aeneas forced alignment (Whisper is deprecated — never use)
- **Clean script blank-line check — non-negotiable**: After saving `03-narration-script-clean.txt`, immediately count its blank-line-separated paragraphs and compare to the structured script scene count. If they differ, a scene has an internal blank line — find and fix it before running TTS or aeneas. A mismatch here cascades into broken video timing.
- **aeneas row count validation**: After `generate_timings.py` produces `audio_timings_new.csv`, immediately check that CSV row count == clean script paragraph count == image count (if images exist). If any of these three disagree, stop and report — never proceed to video assembly. The correct merge strategy: if CSV has N+1 rows for N images, find the split scene (two consecutive rows that belong to the same structured scene) and merge THOSE rows — not the last two rows blindly.
