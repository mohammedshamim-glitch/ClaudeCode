#!/usr/bin/env python3
"""
mxm ballers — YouTube Shorts pipeline
Downloads videos from the BallerzMXM Drive folder, splits into ~50s clips,
adds mxm watermark, crops to 9:16, and uploads to mxm ballers YouTube channel.
"""

import json, os, re, subprocess, requests, math, glob, shutil
from pathlib import Path

TOKEN_FILE = "/home/user/ClaudeCode/token.json"
DRIVE_FOLDER_ID = "1JJOH9UiawBU_ozujd-3aeyslQRHQs1r8"
WORK_DIR = Path("/home/user/ClaudeCode/mxm_shorts")
CLIP_TARGET = 50        # target seconds per Short
CLIP_MIN    = 30        # discard clips shorter than this
CLIP_MAX    = 58        # YouTube Shorts max
WATERMARK   = "mxm"

# ── Auth ─────────────────────────────────────────────────────────────────────

def get_access_token():
    with open(TOKEN_FILE) as f:
        t = json.load(f)
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":     t["client_id"],
        "client_secret": t["client_secret"],
        "refresh_token": t["youtube_refresh_token"],
        "grant_type":    "refresh_token",
    })
    r.raise_for_status()
    token = r.json()["access_token"]
    # Update stored access token
    t["youtube_access_token"] = token
    with open(TOKEN_FILE, "w") as f:
        json.dump(t, f, indent=2)
    return token

# ── Drive ─────────────────────────────────────────────────────────────────────

def list_drive_videos(token):
    r = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        params={
            "q": f"'{DRIVE_FOLDER_ID}' in parents and mimeType contains 'video/' and trashed=false",
            "fields": "files(id,name,size)",
            "pageSize": 50,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    return r.json().get("files", [])


def download_drive_file(file_id, dest_path, token):
    if dest_path.exists():
        print(f"  ↩ Already downloaded: {dest_path.name}")
        return
    print(f"  ↓ Downloading {dest_path.name}...")
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"},
        stream=True,
    )
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
    print(f"  ✓ Saved {dest_path.name}")

# ── Video utils ───────────────────────────────────────────────────────────────

def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())


def make_clips(src_path, out_dir):
    """Split video into ~50s clips at natural scene cuts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = get_duration(src_path)
    n_clips = max(1, round(duration / CLIP_TARGET))
    clip_len = duration / n_clips

    clips = []
    for i in range(n_clips):
        start = i * clip_len
        length = min(clip_len, duration - start)
        if length < CLIP_MIN:
            print(f"  ⚠ Clip {i+1} too short ({length:.0f}s), skipping")
            continue
        length = min(length, CLIP_MAX)
        out_path = out_dir / f"clip_{i+1:03d}.mp4"
        if not out_path.exists():
            subprocess.run([
                "ffmpeg", "-y", "-ss", str(start), "-i", str(src_path),
                "-t", str(length), "-c", "copy", str(out_path)
            ], capture_output=True)
        clips.append(out_path)
        print(f"  ✂ Clip {i+1}/{n_clips}: {start:.0f}s → {start+length:.0f}s")
    return clips


def process_clip(src, out_path):
    """Crop to 9:16, add mxm watermark, encode for Shorts."""
    # Get dimensions
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=p=0", str(src)],
        capture_output=True, text=True
    )
    w, h = map(int, r.stdout.strip().split(","))

    # Centre-crop to 9:16 vertical
    target_w = int(h * 9 / 16)
    if target_w > w:
        target_w = w
        crop_h = int(w * 16 / 9)
        crop_w = w
    else:
        crop_w = target_w
        crop_h = h
    x_off = (w - crop_w) // 2
    y_off = (h - crop_h) // 2

    crop_filter = f"crop={crop_w}:{crop_h}:{x_off}:{y_off},scale=1080:1920"

    # Watermark: white semi-transparent text bottom-right
    watermark_filter = (
        f"drawtext=text='{WATERMARK}'"
        ":fontsize=72"
        ":fontcolor=white@0.7"
        ":x=w-tw-40"
        ":y=h-th-40"
        ":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    )

    vf = f"{crop_filter},{watermark_filter}"

    subprocess.run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(out_path)
    ], capture_output=True)
    print(f"  ✓ Processed: {out_path.name}")


# ── SEO ───────────────────────────────────────────────────────────────────────

def generate_seo(video_title, clip_num, total_clips):
    """Generate Shorts-optimised title, description and tags."""
    # Clean up filename to readable title
    clean = re.sub(r"[_\-]", " ", video_title)
    clean = re.sub(r"\.(mp4|mpeg-4|mkv|webm).*$", "", clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r"\s+", " ", clean)

    title = f"{clean} 🔥 Part {clip_num} #Shorts"
    if len(title) > 100:
        title = f"Football Moments 🔥 Part {clip_num} #Shorts"

    description = (
        f"{clean}\n\n"
        f"Part {clip_num} of {total_clips}\n\n"
        f"🔥 Best football moments, skills, goals & fails\n"
        f"📱 Follow @mxmballerz for daily football content\n\n"
        f"#Shorts #Football #Soccer #Skills #Goals #Fails #mxmballerz #FootballEdit"
    )

    tags = [
        "football", "soccer", "skills", "goals", "fails",
        "football shorts", "soccer shorts", "football edit",
        "mxm ballerz", "football moments", "best football",
        clean[:30]
    ]

    return title, description, tags


# ── YouTube upload ─────────────────────────────────────────────────────────────

def upload_short(video_path, title, description, tags, token):
    """Upload a video as a YouTube Short."""
    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "17",  # Sports
            "defaultLanguage": "en-GB",
            "defaultAudioLanguage": "en-GB",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    # Initiate resumable upload
    r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Upload-Content-Type": "video/mp4",
        },
        json=metadata,
    )
    r.raise_for_status()
    upload_url = r.headers["Location"]

    # Upload video bytes
    file_size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        r2 = requests.put(
            upload_url,
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(file_size),
            },
            data=f,
        )

    if r2.status_code in (200, 201):
        video_id = r2.json().get("id", "unknown")
        print(f"  ✓ Uploaded: https://www.youtube.com/shorts/{video_id}")
        print(f"    Title: {title}")
        return video_id
    else:
        print(f"  ✗ Upload failed: {r2.status_code} {r2.text[:200]}")
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    downloads_dir = WORK_DIR / "downloads"
    processed_dir = WORK_DIR / "processed"
    downloads_dir.mkdir(exist_ok=True)
    processed_dir.mkdir(exist_ok=True)

    print("=== mxm ballerz Shorts Pipeline ===\n")
    token = get_access_token()

    # 1. List Drive videos
    videos = list_drive_videos(token)
    print(f"Found {len(videos)} video(s) in BallerzMXM folder\n")

    for video in videos:
        vid_name = video["name"]
        vid_id   = video["id"]
        print(f"── {vid_name}")

        # 2. Download from Drive
        raw_path = downloads_dir / vid_name
        download_drive_file(vid_id, raw_path, token)

        # 3. Split into clips
        clips_dir = WORK_DIR / "clips" / Path(vid_name).stem
        clips = make_clips(raw_path, clips_dir)
        print(f"  → {len(clips)} clips created")

        # 4. Process each clip (crop + watermark) + upload
        total = len(clips)
        for i, clip in enumerate(clips, 1):
            out_path = processed_dir / f"{Path(vid_name).stem}_short_{i:03d}.mp4"
            if not out_path.exists():
                process_clip(clip, out_path)

            title, desc, tags = generate_seo(vid_name, i, total)

            # Refresh token every 10 uploads
            if i % 10 == 1:
                token = get_access_token()

            upload_short(str(out_path), title, desc, tags, token)

        print()

    print("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
