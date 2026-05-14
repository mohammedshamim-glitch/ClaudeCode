# Claude Code — Project Instructions

## Proactive Improvement — Non-Negotiable

These rules apply on every task, every session, without being asked:

- **End-of-stage review**: After every completed pipeline stage, before moving on, flag anything that could be better. Don't just confirm it's done — give an opinion.
- **Pipeline sequencing**: If a completed stage produces data that would improve a later stage, say so immediately.
- **Continuous improvement**: Every video should be better than the last. After each episode is published, note what could be improved and carry those lessons forward.
- **Spot problems before they happen**: If a skill file, script, or process has a rule that's easy to miss or a step that's fragile, raise it proactively.
- **Never wait to be asked**: If something is suboptimal, say so.

---

## Token Efficiency — Always Apply

- **Skills**: Only invoke a skill when actually executing a full pipeline stage. Never invoke a skill just to answer an informational question about it.
- **File reads**: Read only the specific section or file needed.
- **Drive searches**: Use known folder IDs directly (see below) instead of searching by name every time.
- **Specific Drive queries**: Add `mimeType` and `title contains` filters to avoid large result sets.
- **Trust success**: Don't re-read or re-verify files after a successful write/upload.
- **Git**: Always batch `git add + commit + push` into a single `&&` command.
- **Parallel tool calls**: Always batch independent tool calls in a single message.
- **No mid-task summaries**: Don't summarise what was just done before doing the next thing — just do the next thing.

## Session Learnings Log

Add a bullet here after each session with any new pattern, bug, or convention discovered.

- **UTF-8 decoding**: All Drive text/CSV downloads must use `r.content.decode('utf-8')` — `r.text` silently corrupts em-dashes and £ signs (latin-1 default).
- **File location default**: All assets (images, audio, scripts, videos) are always in Google Drive. Never assume local. Always go to Drive first.
- **YouTube API**: Must be enabled in Google Cloud Console before first upload (project 452685133802). YouTube uses a separate refresh token (`youtube_refresh_token`) from Drive.
- **YouTube auth scope**: `setup_youtube_auth.py` requests both `youtube` and `youtube.force-ssl` scopes — force-ssl is required for posting comments. If comment posting returns 403, re-run auth.
- **Thumbnail in Drive**: Name the thumbnail file "thumbnail" in the episode folder. `upload_youtube.py` finds it automatically.
- **Skills registry**: Skills are registered in `.claude/commands/` (trigger descriptions) — the harness reads commands/, not skills/. Skills content lives in `.claude/skills/`.
- **Mala & Maya TTS voice**: Use `Aoede` voice via `run_tts.py` for all Path A narration.
- **Suno style tag**: Always use `children's nursery rhymes, playful, fun and sing along, upbeat, bouncy, whimsical, kids pop` for Path B songs.
- **Scene splitting**: Story/lyrics scenes are separated by blank lines — never split by word count.

## Known Drive Folder IDs

### Mala and Maya Kids
| Location | Folder ID |
|---|---|
| **Mala and Maya (root)** | `17FIaircel64AqXwAlCafF7Lhv94TQGNk` |
| Hop-Little-Bunnies (active) | `10cjiSaN33FDttrlstNJPQR18FGcd3lHL` |
| Completed | `1kDq0WI-DtNvfvPuXrjbZeG58gDSVVQXY` |
| What-Does-The-Animal-Say | `1lZ9i4EBUcNeqpLDSVT1FKRuDU_5Ne7aS` |
| Mayas-Malas-Feelings-Garden | `1GImkxKYVsG5iCa8W-0ahzYK-74ds1leL` |
| Instructions | `1560C4DKcRv-lugPGSL1yN1IZsUbVZFbq` |

## Project Overview

### Maya & Mala Kids — Disney/Pixar style animated YouTube channel for children.

### Key Scripts
| Script | Purpose |
|---|---|
| `run_tts.py` | Gemini TTS narration generation (Path A) |
| `upload_youtube.py` | Uploads finished video to YouTube with SEO metadata |
| `setup_youtube_auth.py` | One-time YouTube OAuth setup |

### Key Conventions
- All secrets in `token.json` (gitignored) — never hardcode keys
- Audio/text files from Drive always decoded as UTF-8 (`r.content.decode('utf-8')`)
- Content paths: **Path A** (Children's Story, TTS narration) or **Path B** (Nursery Song, Suno)
- Characters: Maya (black pigtails) and Mala (curly brown hair) — always together, equal size
- TTS voice: `Aoede` (warm, Disney-like female) via `run_tts.py`
- Suno style: `children's nursery rhymes, playful, fun and sing along, upbeat, bouncy, whimsical, kids pop`
- Image style: `Disney/Pixar style:` prefix on every prompt
- Video category: Kids & Family (ID: 20), Made for Kids = Yes
- File naming: `01_story_approved.txt`, `02_image_prompts.txt`, `02_video_prompts.txt`, `03_youtube_seo.txt`, `03_thumbnail_prompt.txt`, `04_story_audio.mp3` / `04_song_audio.mp3`
- Development branch: `claude/MayaAndMala`
- Active episode: Hop-Little-Bunnies (folder ID: `10cjiSaN33FDttrlstNJPQR18FGcd3lHL`) — at Step 4 (audio)

## Skills Structure

Skills live flat in `.claude/skills/` — commands registered in `.claude/commands/`:

```
.claude/skills/
├── shared-tts.md
├── shared-video-creator.md
├── shared-youtube-upload.md
├── mala-maya-pipeline.md
├── mala-maya-scriptwriter.md
├── mala-maya-image-prompts.md
├── mala-maya-video-prompts.md
└── mala-maya-seo.md
```
