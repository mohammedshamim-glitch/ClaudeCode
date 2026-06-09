# Claude Code — Project Instructions

## Shorts Cutting Rule — Non-Negotiable

**Always cut Shorts at scene transition boundaries.** Never use a fixed time window. Every Short must start AND end at a detected scene cut so no clip ends mid-action. Use `build_segments()` or equivalent scene-boundary logic — find the nearest scene transition for both the start and end of every clip.

---

## Scheduling Rule — Non-Negotiable

**Never publish a video immediately.** All YouTube uploads (Shorts and long-form) must be scheduled with `privacyStatus: private` and a `publishAt` time that is **at least 2 days from now**. Never set `privacyStatus: public` at upload time. If unsure of the target date, ask before uploading.

---

## Proactive Improvement — Non-Negotiable

These rules apply on every task, every session, without being asked:

- **End-of-stage review**: After every completed pipeline stage, before moving on, flag anything that could be better. Don't just confirm it's done — give an opinion.
- **Pipeline sequencing**: If a completed stage produces data that would improve a later stage, say so immediately. Example: Whisper timings ready → flag that SEO chapters and SRT should use them before upload.
- **Continuous improvement**: Every video should be better than the last. After each full episode is published, note what could be improved — SEO, scene pacing, image quality, caption accuracy — and carry those lessons forward.
- **Spot problems before they happen**: If a skill file, script, or process has a rule that's easy to miss or a step that's fragile, raise it proactively. Don't wait for a failed output to prove the point.
- **Never wait to be asked**: If something is suboptimal, say so. Sham should not have to find the gaps — that is my job as the expert in this pipeline.

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
- **SEO parser**: `06-seo-metadata.txt` uses `━━━` separator lines — requires a line-by-line state machine parser, not regex on separator chars.
- **YouTube API**: Must be enabled in Google Cloud Console before first upload (project 452685133802). YouTube uses a separate refresh token (`youtube_refresh_token`) from Drive.
- **Audio subfolder**: For the S&P 500 war episode, audio is in an `Audio` subfolder as `.wav`, not `narration.mp3` in the root.
- **File location default**: All assets (images, audio, scripts, CSVs, videos) are always in Google Drive. Never assume local. Never search locally first. Always go to Drive.
- **No SRT generation**: YouTube auto-generates captions. Never run generate_srt.py. Set `defaultLanguage` and `defaultAudioLanguage` to `en-GB` on upload — that's all that's needed.
- **Pinned comment**: upload_youtube.py auto-posts the pinned comment after upload. BUT it only works on public/unlisted videos — not private/scheduled. For scheduled videos, post the comment manually in Studio once live, then pin it (3 dots → Pin) within 60 min.
- **Auto-scheduling**: upload_youtube.py automatically schedules publish for next Wednesday at 4pm UK time, minimum 2 days after upload. No `--privacy` flag needed — scheduling is always on.
- **Filename = title slug**: Video and thumbnail filenames must match the video title (slugified). This is SEO best practice. upload_youtube.py handles this automatically.
- **Thumbnail in Drive**: Name the thumbnail file "thumbnail" in the episode folder. upload_youtube.py will find it and upload it automatically alongside the video.
- **KB movement file**: Old `05-kb-movements.txt` has verbose descriptions — `movement_to_effect_idx()` should return `None` for unrecognised text and fall back to cycling, not default to pan left to right.
- **KB sample image**: Use file ID `17FRRCFFkVRQUuSC8t7fsPEmjSEgzd88p` from the S&P 500 vs Stocks episode for future KB sample generation.
- **mxm ballers music**: Two royalty-free tracks stored at `mxm_shorts/music/upbeat_background_1.mp3` (2m22s) and `upbeat_background_2.mp3` (1m16s) — use these when replacing audio on Shorts. Loop/trim to fit clip length with ffmpeg `-stream_loop -1`.
- **YouTube Brand Account**: Monkey See Money is a Brand Account on the same Google email as Digital Fusion. Always run `setup_youtube_auth.py` and select **Monkey See Money** — not the personal/Digital Fusion account. The wrong channel auth will silently upload to the wrong channel.
- **Skip-a-Wednesday scheduling**: To target the Wednesday after next, temporarily set `MIN_DAYS_BUFFER = 4` in `upload_youtube.py` before running, then reset to `2` immediately after. With buffer=4, today (Mon) + 4 days = Fri, next Wednesday = the one after next.
- **YouTube auth scope**: `setup_youtube_auth.py` now requests both `youtube` and `youtube.force-ssl` scopes — the force-ssl scope is required for posting comments. If comment posting returns 403, re-run auth.
- **upload_youtube.py rename bug**: The slug rename must happen AFTER download, not before. File is downloaded directly to the slugged filename path now — do not reintroduce a pre-download rename.
- **Thumbnail mime type**: Thumbnails may be PNG not JPEG. upload_youtube.py now reads the actual Drive mimeType and sends the correct Content-Type header. Do not hardcode `image/jpeg`.
- **AI video clips pipeline**: `create_video_from_clips.py` replaces `create_video_kb.py` when using AI-generated video clips instead of KB-effect images. Looks for `Videos` subfolder, `audio_timings_new.csv`, and audio file. Slows clips where scene > clip duration, trims where scene < clip duration.
- **Monkey action rule**: Every monkey scene must show the monkey mid-action with a prop (pressing button, holding umbrella, looking through binoculars, etc.). Never just standing. Enforced in VISUAL-RULES.md and SKILL.md.
- **YouTube transcript extraction**: yt-dlp and youtube-transcript-api both get 403 from this server's IP — YouTube blocks it. Use Gemini API instead: `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}` with `{"file_data": {"mime_type": "video/*", "file_uri": "https://www.youtube.com/watch?v=VIDEO_ID"}}` as a part alongside the text prompt. Gemini natively reads YouTube URLs and returns full transcripts. Use model `gemini-2.5-flash` — `gemini-2.0-flash` may hit quota limits.
- **Competitor video research**: To find a competitor video ID, use the YouTube Data API search endpoint with a refreshed `youtube_refresh_token`: `GET https://www.googleapis.com/youtube/v3/search?part=snippet&q=QUERY&type=video` with Bearer auth. Then pass the video ID to Gemini for transcript extraction.
- **Script style — character-driven**: Scripts perform better with named characters (e.g. Jake and Marcus) rather than abstract "you vs you" comparisons. The Wealth Logic "Real Estate vs Stocks" format (1.48M views) uses two characters to make the emotional journey concrete and followable. Adopt this structure for comparison videos.
- **Script adaptation workflow**: Find the top-performing competitor video on a topic → extract transcript via Gemini → adapt to UK (swap $ for £, add ISA/CGT/Section 24/stamp duty, change characters/scenarios) → keep the proven emotional beats and structure intact.

## Known Drive Folder IDs

### Monkey Finance / Monkey See Money
| Location | Folder ID |
|---|---|
| **Monkey See Money (default root)** | `1N0fFEokv69CVVMbSFbIi_FFDsab3kadR` |
| Monkey Finance (old root) | `1Z-aB7dKK9T9EpndozU-6lAvbxdo6yknS` |
| S&P 500 vs Picking Your Own Stocks (53 scenes) | `1VSu4FuGUQhDxk6yC5HAjnze6YetAEecO` |
| S&P 500 All-Time High During War (51 scenes) | `1fFJnQTbnJ6hAKmD5sXDhVFdk77U_f52U` |
| The Savings Tax Trap | `1lfFqd3FuqEXJx5DNMKP1YqnXTK1_W2dc` |
| Property vs Stocks — The Real Math (UK) | `14wJDYLxkPX2_ltbwxv8VS8b2kk4orMVq` |

## Project Overview

### Monkey Finance — automated YouTube video production pipeline.

### Key Scripts
| Script | Purpose |
|---|---|
| `generate_timings_whisper.py` | Whisper word-level timestamps → `audio_timings_new.csv` |
| `create_video_kb.py` | Assembles images + audio into MP4 with Ken Burns effects |
| `upload_youtube.py` | Uploads finished video to YouTube with SEO metadata |
| `setup_youtube_auth.py` | One-time YouTube OAuth setup |
| `run_tts.py` | Text-to-speech narration generation |

### Key Conventions
- All secrets in `token.json` (gitignored) — never hardcode keys
- Audio/text files from Drive always decoded as UTF-8 (`r.content.decode('utf-8')`)
- Scene splits by blank line in narration script (one paragraph = one scene)
- KB effects: 25% of scenes (every 4th), 4 directional pans only (pan L→R, R→L, T→B, B→T)
- Image prompts: 20% border, content within central 60% of frame
- Development branch: `claude/MonkeySeeMoney`
- Whisper model: base (139MB at `~/.cache/whisper/base.pt`)

## Skills Structure

Skills live flat in `.claude/skills/` — prefixed by project:

```
.claude/skills/
├── shared-tts.md
├── shared-video-creator.md
├── shared-youtube-upload.md
├── monkey-finance-pipeline.md
├── monkey-finance-trends.md
├── monkey-finance-scriptwriter.md
├── monkey-finance-image-prompts.md
└── monkey-finance-seo-thumbnail.md
```
