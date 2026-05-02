# Monkey Finance TTS — Audio Generation Skill

Convert a Monkey Finance narration script from Google Drive into an MP3 using Gemini TTS, then upload it back to the correct Drive folder automatically.

## Quick usage

When the user asks to generate audio for a Monkey Finance video, do the following:

### 1. Find the episode folder
Search Google Drive for the episode folder inside the **Monkey Finance** root folder (ID: `1Z-aB7dKK9T9EpndozU-6lAvbxdo6yknS`):
- Use `search_files` with: `parentId = '1Z-aB7dKK9T9EpndozU-6lAvbxdo6yknS' and title contains '<episode keyword>'`

### 2. Find the narration script
Search inside the episode folder for `narration_script.txt`:
- Use `search_files` with: `parentId = '<episode_folder_id>' and title contains 'narration'`
- Note the file ID.

### 3. Run the TTS pipeline
```bash
python3 /home/user/ClaudeCode/run_tts.py <narration_file_id> <episode_folder_id> narration.mp3
```

This will:
- Download the narration from Drive
- Chunk it into ~150-word segments
- Generate audio via **Gemini 3.1 Flash TTS** using the **Orus** voice
- Merge chunks into a single WAV, then convert to MP3
- Upload `narration.mp3` back into the episode folder automatically

## Config reference

| Setting | Value |
|---|---|
| Script | `/home/user/ClaudeCode/run_tts.py` |
| TTS Model | `gemini-3.1-flash-tts-preview` |
| Voice | `Orus` |
| Chunk size | 150 words |
| Output format | MP3 (128kbps) |
| Auth | OAuth2 refresh token — fully automatic, no login needed |
| Token file | `/home/user/ClaudeCode/token.json` |
| Gemini key | Set in `run_tts.py` or via `GEMINI_API_KEY` env var |

## Monkey Finance Drive structure

```
Monkey Finance/                          (ID: 1Z-aB7dKK9T9EpndozU-6lAvbxdo6yknS)
└── YYYY-MM-DD - <Episode Title>/
    ├── narration_script.txt             ← input
    ├── narration.mp3                    ← output (uploaded here)
    └── video_prompts.txt
```

## Notes
- Auth is fully automated via saved refresh token — no browser login needed after initial setup
- If token expires or is revoked, re-run `python3 /home/user/ClaudeCode/setup_auth.py`
- To use a different voice, update `VOICE` in `run_tts.py` (available: Aoede, Charon, Fenrir, Kore, Puck, Orus)
