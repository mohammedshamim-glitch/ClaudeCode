# Monkey Finance — Video Creator Skill

Assemble images and narration audio from a Drive episode folder into a finished 1920×1080 MP4 with Ken Burns motion, crossfade transitions, and karaoke-style word-highlight subtitles.

---

## Pipeline position

Run **after** images are uploaded to Drive and `narration.mp3` exists in the episode folder.

Prerequisite order:
1. TTS → `narration.mp3` in Drive
2. Images uploaded to Drive `Images/` subfolder
3. **`generate_timings.py`** → `audio_timings_new.csv` (aeneas forced alignment)
4. **`create_sample.py`** → 30-second preview for approval
5. **`create_video_kb.py`** → finished MP4

---

## Step 1 — Generate scene timings

```bash
python3 /home/user/ClaudeCode/generate_timings.py <episode_folder_id>
```

Uses **aeneas forced alignment** — syncs source text directly to audio using espeak + DTW on MFCC features. No re-transcription, no drift. Outputs `audio_timings_new.csv` with columns: `scene`, `narration_excerpt`, `words`, `duration_seconds`, `start_time`, `end_time`, `start_seconds`, `end_seconds`.

Script priority for narration text (first match wins):
1. `03b-narration-sentences.txt`
2. `03-narration-script-clean.txt`
3. `03-narration-script-clean-FINAL.txt`
4. `narration_script.txt`

---

## Step 2 — Preview sample (always do this first)

Before a full render, generate a 30-second preview to check KB motion, subtitles, and transitions:

```bash
python3 /home/user/ClaudeCode/create_sample.py <episode_folder_id> --crossfade --output=sample_crossfade.mp4
```

Uploads to the episode Drive folder. Confirm with Sham before running the full render.

Flags:
- `--crossfade` — 0.3s dissolve transitions (preferred style)
- `--output=filename.mp4` — output filename in Drive

---

## Step 3 — Full video render

```bash
# Standard: Ken Burns + karaoke subtitles
python3 /home/user/ClaudeCode/create_video_kb.py <episode_folder_id> --subs

# No subtitles
python3 /home/user/ClaudeCode/create_video_kb.py <episode_folder_id>

# Static (no Ken Burns)
python3 /home/user/ClaudeCode/create_video_kb.py <episode_folder_id> --no-kb
```

Auto-names the output after the Drive folder name. Uploads finished MP4 back to the episode folder.

---

## Config reference

### Video
| Setting | Value |
|---|---|
| Resolution | 1920×1080 |
| FPS | 30 |
| Video codec | H.264 (libx264), CRF 23, preset fast |
| Audio codec | AAC 192kbps |
| Last scene bonus | +5s (image lingers after narration ends) |

### Ken Burns
| Setting | Value |
|---|---|
| Frequency | Every 4th scene (`i > 0 and i % 4 == 1`) — never scene 1 |
| Zoom scale | 1.2× (image scaled to 120%, ~83% of image visible, panning across it) |
| Directions | Pan L→R, R→L, T→B, B→T (cycles automatically) |
| Override file | `05-kb-movements.txt` in episode folder (optional) |

### Transitions
| Setting | Value |
|---|---|
| Preferred style | Crossfade 0.3s dissolve |
| Available in | `create_sample.py --crossfade` (confirmed working) |
| Full render | Hard cuts currently; crossfade to be added to `create_video_kb.py` |

### Karaoke subtitles (`--subs`)
| Setting | Value |
|---|---|
| Method | PIL RGBA frames composited as MOV overlay (`ffmpeg overlay` filter) |
| Font | LiberationSans-Bold, 80pt |
| Font path | `/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf` |
| Words per phrase | 4 |
| Active word highlight | Solid green rounded rectangle `(0, 200, 0, 255)` |
| Box horizontal padding | 18px |
| Box vertical padding | 10px |
| Box corner radius | 8px |
| Text colour | White with 2px black stroke |
| Margin from bottom | 90px |
| Box y-positioning | `y1 = y_text + bb[1] - pad`, `y2 = y_text + bb[3] + pad` (raw `getbbox()` values) |
| Anchor y_text | `h - SUB_MARGIN_V - max(bb[3] for all words)` — glyph bottom sits at margin |
| Timing source | `audio_timings_new.csv` — requires `start_seconds`/`end_seconds` columns |

---

## Drive folder structure expected

```
Episode Folder/
├── Images/                       ← sorted by leading number in filename (1_xx, 2_xx…)
│   ├── 1_1.1.png
│   └── ...
├── narration.mp3                 ← TTS output
├── audio_timings_new.csv         ← aeneas output (required for --subs)
├── 05-kb-movements.txt           ← optional KB direction overrides
├── sample_crossfade.mp4          ← 30s preview for approval
└── <folder name>.mp4             ← finished video
```

Image sort order: **leading number in filename** (`re.match(r'^(\d+)_', name)`). Not by modifiedTime.

---

## Known issues / gotchas

- **`--subs` requires `start_seconds` column**: Old `auto_timings.csv` doesn't have it. If missing, re-run `generate_timings.py` to get `audio_timings_new.csv`.
- **PIL box clipping text**: Box bottom must use raw `bb[3]` from `font.getbbox()`, not `bb[3] - bb[1]`. The delta subtracts the top offset twice and clips letter bottoms.
- **OAuth 7-day expiry**: Happens when Google Cloud app is in Testing mode. Fix once: Cloud Console → OAuth consent screen → Publish App → re-run `setup_auth.py`. Token is then permanent.
- **KB movements file**: `movement_to_effect_idx()` returns `None` for unrecognised text — caller falls back to cycling. Never hardcode a default direction.
- **generate_timings.py content check**: After the rename commit the file briefly reverted to old proportional code. Verify it imports `aeneas` — if not, restore: `git show 2e91d8b:generate_timings_whisper.py > generate_timings.py`.
- **Pillow install**: `pip install Pillow` — required for `create_sample.py` and `--subs` in `create_video_kb.py`.
