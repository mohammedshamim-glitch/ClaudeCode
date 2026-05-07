# Claude Code — Project Instructions

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
- **Drive MCP vs raw API**: MCP tool returns `title` field; raw Drive API returns `name` field — don't mix them.
- **KB movement file**: Old `05-kb-movements.txt` has verbose descriptions — `movement_to_effect_idx()` should return `None` for unrecognised text and fall back to cycling, not default to pan left to right.
- **KB sample image**: Use file ID `17FRRCFFkVRQUuSC8t7fsPEmjSEgzd88p` from the S&P 500 vs Stocks episode for future KB sample generation.

## Known Drive Folder IDs

| Episode | Folder ID |
|---|---|
| S&P 500 vs Picking Your Own Stocks (53 scenes) | `1VSu4FuGUQhDxk6yC5HAjnze6YetAEecO` |
| S&P 500 All-Time High During War (51 scenes) | `1fFJnQTbnJ6hAKmD5sXDhVFdk77U_f52U` |

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
