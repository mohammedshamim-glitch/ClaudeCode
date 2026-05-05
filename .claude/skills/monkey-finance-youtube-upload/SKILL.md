# Monkey Finance — YouTube Upload Skill

Upload a finished Monkey Finance episode to YouTube with full SEO metadata automatically applied.

---

## What This Skill Does

1. Downloads the finished video (`video_kb.mp4`) from the episode's Google Drive folder
2. Reads and parses `06-seo-metadata.txt` — extracts title, description, tags, and chapter timestamps
3. Uploads the video to YouTube via the Data API v3 (resumable upload)
4. Sets all metadata, category (Education), and language (en-GB)
5. Returns the YouTube watch URL and Studio link

---

## Trigger

Use this skill whenever Sham says:
- "upload to YouTube"
- "publish the video"
- "upload the episode"
- "send it to YouTube"
- "push it to YouTube"

---

## Pre-flight Checklist — Verify Before Running

Before uploading, confirm:

- [ ] `06-seo-metadata.txt` exists in the episode Drive folder
- [ ] `video_kb.mp4` exists in the episode Drive folder
- [ ] YouTube is authenticated (`youtube_refresh_token` is set in `token.json`)
- [ ] Privacy setting confirmed with Sham (default: **private** — always start private)

If `youtube_refresh_token` is missing from `token.json`, YouTube auth has not been done yet. Run:
```
python3 /home/user/ClaudeCode/setup_youtube_auth.py
```
Follow the on-screen instructions (one-time setup, takes ~2 minutes).

---

## Running the Upload

```bash
python3 /home/user/ClaudeCode/upload_youtube.py <episode_folder_id> [--privacy private|unlisted|public]
```

**Privacy options:**
| Option | Use when |
|--------|----------|
| `private` | Default — upload and review in Studio before anyone sees it |
| `unlisted` | Share with a specific person (e.g. for review) |
| `public` | Go live immediately |

**Always default to `private` unless Sham explicitly says otherwise.**

---

## What Gets Set Automatically

| Field | Source |
|-------|--------|
| Title | Primary title from `06-seo-metadata.txt` |
| Description | Full description block + chapter timestamps |
| Tags | All tags from the SEO package (up to 500 chars) |
| Category | Education (ID 27) |
| Language | en-GB |
| Privacy | As specified (default: private) |
| Made for kids | No |

---

## After Upload — Always Tell Sham

Report back with:
- YouTube watch URL
- YouTube Studio URL (for thumbnail upload and final review)
- Reminder to upload the thumbnail manually in Studio (the API requires a verified account for custom thumbnails)

Example:
```
✓ Uploaded to YouTube (private)
Watch: https://www.youtube.com/watch?v=XXXXX
Studio: https://studio.youtube.com/video/XXXXX/edit

Next steps in Studio:
1. Upload the thumbnail (from the SEO package thumbnail brief)
2. Add end screens and cards
3. Set the publish date or go public when ready
```

---

## Thumbnail Note

YouTube's API only allows custom thumbnail uploads for **verified channels**. If the channel is verified, the thumbnail can be uploaded programmatically — ask Sham if he wants this added. Otherwise, upload manually in YouTube Studio using the AI thumbnail prompt from `06-seo-metadata.txt`.

---

## Error Handling

| Error | Fix |
|-------|-----|
| `youtube_refresh_token` missing | Run `setup_youtube_auth.py` |
| `06-seo-metadata.txt` not found | Run Stage 4 (SEO skill) first |
| `video_kb.mp4` not found | Run Stage 6 (video assembly) first |
| 403 on upload | Check YouTube account has upload permissions; channel must not be restricted |
| Title parse fails | Open `06-seo-metadata.txt` and check PRIMARY section format |
