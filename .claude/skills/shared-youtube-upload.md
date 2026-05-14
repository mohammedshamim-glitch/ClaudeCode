# YouTube Upload — Shared Skill

Upload a finished video to YouTube with full SEO metadata automatically applied. Works for any channel configured in `token.json`.

---

## What This Skill Does

1. Downloads the finished video from the episode's Google Drive folder
2. Reads and parses the SEO metadata file — extracts title, description, tags, and chapter timestamps
3. Uploads the video to YouTube via the Data API v3 (resumable upload)
4. Sets all metadata, category, and language
5. Returns the YouTube watch URL and Studio link

---

## Trigger

Use this skill whenever the user says:
- "upload to YouTube"
- "publish the video"
- "upload the episode"
- "send it to YouTube"
- "push it to YouTube"

---

## Project-specific settings

| Project | Video filename | SEO metadata file | Category | Language |
|---|---|---|---|---|
| **Monkey Finance** | `<folder-name>.mp4` | `06-seo-metadata.txt` | Education (27) | en-GB |
| **Mala and Maya** | `<folder-name>.mp4` | `03_youtube_seo.txt` | Kids & Family (20) | en-GB |

---

## Pre-flight Checklist — Verify Before Running

Before uploading, confirm:

- [ ] SEO metadata file exists in the episode Drive folder (see table above for filename)
- [ ] Finished video MP4 exists in the episode Drive folder
- [ ] YouTube is authenticated (`youtube_refresh_token` is set in `token.json`)
- [ ] Privacy setting confirmed (default: **private** — always start private)

If `youtube_refresh_token` is missing, run:
```
python3 /home/user/ClaudeCode/setup_youtube_auth.py
```

---

## Running the Upload

```bash
python3 /home/user/ClaudeCode/upload_youtube.py <episode_folder_id> [--privacy private|unlisted|public]
```

**Always default to `private` unless the user explicitly says otherwise.**

---

## What Gets Set Automatically

| Field | Source |
|-------|--------|
| Title | From SEO metadata file |
| Description | Full description block + chapter timestamps |
| Tags | All tags from the SEO package (up to 500 chars) |
| Category | Per project (see table above) |
| Language | en-GB |
| Privacy | Scheduled (auto-publishes on target date) |
| Thumbnail | Uploaded automatically if named `thumbnail` in episode folder |
| Pinned comment | Posted automatically if present in SEO metadata file |

---

## YouTube Brand Account

Always ensure auth is set to the correct channel. Run `setup_youtube_auth.py` and select the right account:
- **Monkey Finance** → Monkey See Money
- **Mala and Maya** → Mala and Maya Kids (or whichever channel is configured)

Wrong channel auth will silently upload to the wrong channel.

---

## After Upload — Always Report Back

Report with:
- YouTube watch URL
- YouTube Studio URL
- Scheduled publish date/time
- Reminder to **pin the comment** in Studio (3 dots → Pin) within 60 minutes of going live

---

## Error Handling

| Error | Fix |
|-------|-----|
| `youtube_refresh_token` missing | Run `setup_youtube_auth.py` |
| SEO metadata file not found | Run the SEO skill for the project first |
| Video MP4 not found | Run video assembly first |
| 403 on upload | Check YouTube account has upload permissions |
| 403 on comment | Re-run `setup_youtube_auth.py` (needs `youtube.force-ssl` scope) |
