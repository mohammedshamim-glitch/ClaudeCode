# Monkey Finance TTS — Audio Generation Skill

Convert the clean narration script from Google Drive into an MP3 using Gemini TTS, then upload it back to the episode Drive folder automatically.

## Pipeline position

Stage 4 — runs after image prompts (Stage 3) are approved by Sham.

## Quick usage

```bash
python3 /home/user/ClaudeCode/run_tts.py <narration_file_id> <episode_folder_id> narration.mp3
```

Where `narration_file_id` is the Drive file ID of `03-narration-script-clean.txt`.

This will:
- Download the clean narration from Drive
- Check Drive `tts_chunks/` subfolder for existing chunks and download them before generating
- Chunk it into balanced ~150-word segments
- Generate audio via Gemini TTS (Orus voice) — skips chunks already on disk
- Upload each chunk to Drive `tts_chunks/` immediately after generating (session-restart safe)
- Pace-lock: slow fast chunks down to the median wpm ceiling via `ffmpeg atempo` — slow chunks kept at their natural pace, never sped up
- Merge chunks into a single WAV, then convert to MP3
- Upload `narration.mp3` back into the episode folder automatically

## Config reference

| Setting | Value |
|---|---|
| Script | `/home/user/ClaudeCode/run_tts.py` |
| TTS Model | `gemini-2.5-flash-preview-tts` |
| Voice | `Orus` |
| Chunk size | ~150 words (balanced) |
| Output format | MP3 |
| Auth | OAuth2 refresh token — fully automatic |
| Token file | `/home/user/ClaudeCode/token.json` |
| Gemini key | `gemini_tts_api_key` from `token.json` (falls back to `gemini_api_key`) |

## Resume behaviour

Chunks are saved both locally (`/home/user/ClaudeCode/tts_chunks/`) and to a `tts_chunks/` subfolder inside the episode Drive folder. On re-run, Drive is checked first — existing chunks are downloaded before generating. This means chunks survive session restarts without wasting quota. Do NOT delete chunk files from Drive until the episode is fully assembled and uploaded.

## Daily quota

The free-tier `gemini-2.5-flash-preview-tts` hits quota after ~13 chunks (~2,000 words). If quota is hit, wait until the next day (resets ~midnight Pacific / ~8am UK) and re-run. Completed chunks are safe in Drive.

## Drive folder structure

```
YYYY-MM-DD — Episode Title/
├── tts_chunks/                    ← chunk WAVs backed up here after generation
│   ├── <run_id>_chunk_01.wav
│   └── ...
├── 00-source-transcript-wealth-logic-original.txt
├── 00b-character-references.txt   (if named characters used)
├── 02-narration-script-structured.txt
├── 03-narration-script-clean.txt  ← TTS input
├── 04-image-prompts.txt
└── narration.mp3                  ← TTS output
```

## No SRT generation — ever

YouTube auto-generates captions. Never run `generate_srt.py`. Set `defaultAudioLanguage` to `en-GB` on upload — that's all that's needed (handled automatically by `upload_youtube.py`).

## Approval gate

After upload, confirm with Sham:
> *"Stage 4 complete. `narration.mp3` uploaded to Drive. Ready to move to Stage 5a (timings + SEO)?"*

Wait for Sham's go-ahead before proceeding.
