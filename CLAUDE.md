# Claude Code — Project Instructions

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
- **YouTube Brand Account**: Monkey See Money is a Brand Account on the same Google email as Digital Fusion. Always run `setup_youtube_auth.py` and select **Monkey See Money** — not the personal/Digital Fusion account. The wrong channel auth will silently upload to the wrong channel.
- **Skip-a-Wednesday scheduling**: To target the Wednesday after next, temporarily set `MIN_DAYS_BUFFER = 4` in `upload_youtube.py` before running, then reset to `2` immediately after. With buffer=4, today (Mon) + 4 days = Fri, next Wednesday = the one after next.
- **YouTube auth scope**: `setup_youtube_auth.py` now requests both `youtube` and `youtube.force-ssl` scopes — the force-ssl scope is required for posting comments. If comment posting returns 403, re-run auth.
- **upload_youtube.py rename bug**: The slug rename must happen AFTER download, not before. File is downloaded directly to the slugged filename path now — do not reintroduce a pre-download rename.
- **Thumbnail mime type**: Thumbnails may be PNG not JPEG. upload_youtube.py now reads the actual Drive mimeType and sends the correct Content-Type header. Do not hardcode `image/jpeg`.
- **AI video clips pipeline**: `create_video_from_clips.py` replaces `create_video_kb.py` when using AI-generated video clips instead of KB-effect images. Looks for `Videos` subfolder, `audio_timings_new.csv`, and audio file. Slows clips where scene > clip duration, trims where scene < clip duration.
- **Monkey action rule**: Every monkey scene must show the monkey mid-action with a prop (pressing button, holding umbrella, looking through binoculars, etc.). Never just standing. Enforced in VISUAL-RULES.md and SKILL.md.
- **Script data density**: Scripts must lead with specific UK numbers, not generalisations. Use realistic starting amounts (e.g. £25k deposit on a £100k property, not £290k all-in). Every section must include named figures: pound values, percentages, years, milestone outcomes (year 5, 10, 20, 25). Market crash data must cite actual percentages and recovery timelines (2008: S&P fell 49%, recovered 2013; COVID 2020: fell 34%, recovered in 5 months). Never write a finance comparison without pound-for-pound milestone tables. Scripts that are wordy but data-light will be rejected.
- **Property vs stocks numbers** (£25k deposit on £100k BTL): Stamp duty: £3k (3% BTL surcharge). Mortgage: £75k at 5.5% IO = £344/month. Rent at 6% yield = £500/month. With Section 24 at 40% tax = -£127/month net. Property at 3.5%/yr: Year 5 equity £43.8k, Year 10 £66k, Year 15 £93k, Year 20 £124k, Year 25 £161k (before CGT £32k = net £129k). ISA at 8%/yr: Year 5 £36.7k, Year 10 £54k, Year 15 £79.3k, Year 20 £116.5k, Year 25 £171.2k (tax free). ISA wins at year 20+ after CGT.

## Known Drive Folder IDs

| Location | Folder ID |
|---|---|
| **Monkey See Money (default root)** | `1N0fFEokv69CVVMbSFbIi_FFDsab3kadR` |
| Monkey Finance (old root) | `1Z-aB7dKK9T9EpndozU-6lAvbxdo6yknS` |
| S&P 500 vs Picking Your Own Stocks (53 scenes) | `1VSu4FuGUQhDxk6yC5HAjnze6YetAEecO` |
| S&P 500 All-Time High During War (51 scenes) | `1fFJnQTbnJ6hAKmD5sXDhVFdk77U_f52U` |
| The Savings Tax Trap | `1lfFqd3FuqEXJx5DNMKP1YqnXTK1_W2dc` |

## Project Overview

Monkey Finance — automated YouTube video production pipeline.

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
- Development branch: `claude/general-session-8o65N`
- Whisper model: base (139MB at `~/.cache/whisper/base.pt`)
