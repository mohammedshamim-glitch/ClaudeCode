# mxm-ballers skill

Run the full mxm ballerz YouTube Shorts pipeline: download football videos from Google Drive, split into ~50s clips, add mxm watermark, crop to 9:16, and upload to the mxm ballers YouTube channel.

## Trigger

User says anything like:
- "run mxm ballers"
- "create shorts from the ballerz folder"
- "process the mxm ballers videos"
- "upload new shorts to mxm ballers"

## Config

| Setting | Value |
|---|---|
| Drive folder | `BallerzMXM` — ID `1JJOH9UiawBU_ozujd-3aeyslQRHQs1r8` |
| YouTube channel | mxm ballers (authenticated via `token.json`) |
| Clip length | 30–55s — always cuts at natural scene boundaries, never mid-clip |
| Scene detection | Two-pass: major threshold 0.55, fine threshold 0.25 |
| Watermark | `mxm` — white, semi-transparent, bottom-right |
| Format | 9:16 vertical (1080×1920), centre-crop from 16:9 source |
| Category | Sports (ID 17) |
| Language | en-GB |

## Steps

1. **Check Drive folder** — list all video files in `BallerzMXM` (skips Shorts/Completed subfolders)
2. **Download** — pull each video from Drive to `/home/user/ClaudeCode/mxm_shorts/downloads/`
3. **Split** — two-pass scene detection (major chapters + fine cuts) groups clips into 30–55s segments, never cuts mid-scene
4. **Process** — for each clip: centre-crop to 9:16, scale to 1080×1920, overlay `mxm` watermark (no player names, no fade out)
5. **Save to Drive** — clips go to `BallerzMXM/Shorts/{Video Title}/`
6. **Move to Completed** — once all clips saved, source video moves to `BallerzMXM/Completed/`
7. **STOP — confirm with user before any YouTube upload**

## Run

```bash
cd /home/user/ClaudeCode && python3 mxm_ballers_pipeline.py
```

## Drive folder structure

```
BallerzMXM/
├── Shorts/
│   ├── {Video Title 1}/   ← processed 50s clips
│   └── {Video Title 2}/
├── Completed/             ← original long videos moved here after processing
└── (new videos dropped here to be picked up)
```

## Add new videos

1. User downloads video from their @rm26hd channel (YouTube Studio app → Download)
2. User uploads to Google Drive → `BallerzMXM/` root (NOT into Shorts or Completed)
3. Run this skill — pipeline picks it up, processes it, then moves it to Completed

## SEO pattern

- **Title**: `{clean video title} 🔥 Part {N} #Shorts`
- **Description**: title + part info + football hashtags + @mxmballerz CTA
- **Tags**: football, soccer, skills, goals, fails, football shorts, mxm ballerz, etc.

## Notes

- Already-downloaded files are skipped (safe to re-run)
- Already-processed clips are skipped (safe to re-run)
- Token is refreshed every 10 uploads to avoid expiry
- Videos stay in Drive — nothing is deleted
