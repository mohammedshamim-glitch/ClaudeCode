# Claude Code — Project Instructions

## Token Efficiency — Always Apply

Be conservative with context usage on every task:

- **Skills**: Only invoke a skill when actually executing a full pipeline stage. Never invoke a skill just to answer an informational question about it.
- **File reads**: Read only the specific section or file needed. Use `grep` to find the relevant lines before committing to a full file read.
- **Reference files**: Do not load all reference files by default. Read only the one that contains what is needed for the immediate task.
- **Script runs**: Only run scripts when the user explicitly asks to build or generate something.
- **Simple requests**: Answer directly from context or a single targeted lookup — no multi-file loading for straightforward questions.

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
- KB effects: 25% of scenes (every 4th), 4 directional pans only
- Image prompts: 20% border, content within central 60% of frame
- Development branch: `claude/general-session-8o65N`
