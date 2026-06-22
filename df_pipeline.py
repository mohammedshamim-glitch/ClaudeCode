#!/usr/bin/env python3
"""
Digital Fusion — Full Episode Pipeline
Usage: python3 df_pipeline.py <drive_file_id> <original_filename>
"""
import json, os, sys, re, io, time, requests, subprocess, tempfile
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import imageio_ffmpeg

TOKEN_FILE = "/home/user/ClaudeCode/token.json"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
PROCESSED_FOLDER_ID = "1q80MPi_hAfcCLeKsYCBOB-_vrBJCV26z"
BOLD_RE = re.compile(r'\*\*(.+?)\*\*')


# ── Credentials ────────────────────────────────────────────────────────────────

def load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)

def get_access_token(tok):
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": tok["client_id"], "client_secret": tok["client_secret"],
        "refresh_token": tok["digital_fusion_refresh_token"], "grant_type": "refresh_token",
    })
    r.raise_for_status()
    return r.json()["access_token"]


# ── Scheduling ─────────────────────────────────────────────────────────────────

def next_thursday_6pm_bst():
    now = datetime.utcnow()
    days_ahead = (3 - now.weekday()) % 7
    if days_ahead < 2:
        days_ahead += 7
    target = (now + timedelta(days=days_ahead)).replace(hour=17, minute=0, second=0, microsecond=0)
    return target.strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ── Drive helpers ───────────────────────────────────────────────────────────────

def drive_download(file_id, dest, at):
    print(f"  Downloading from Drive…")
    r = requests.get(f"https://www.googleapis.com/drive/v3/files/{file_id}",
                     params={"alt": "media"},
                     headers={"Authorization": f"Bearer {at}"}, stream=True)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            f.write(chunk)
    print(f"  Downloaded: {os.path.getsize(dest)//1024//1024} MB")

def drive_create_folder(name, parent_id, at):
    r = requests.post("https://www.googleapis.com/drive/v3/files",
                      headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json"},
                      json={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]})
    return r.json()["id"]

def drive_upload(path, filename, folder_id, at, mime="video/mp4"):
    size = os.path.getsize(path)
    r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
                      headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json",
                               "X-Upload-Content-Type": mime, "X-Upload-Content-Length": str(size)},
                      json={"name": filename, "parents": [folder_id]})
    with open(path, "rb") as f:
        data = f.read()
    r2 = requests.put(r.headers["Location"],
                      headers={"Content-Type": mime, "Content-Length": str(size)}, data=data)
    fid = r2.json()["id"]
    print(f"  Saved to Drive: {filename} → {fid}")
    return fid

def drive_upload_doc(html_bytes, filename, folder_id, at):
    """Upload HTML as Google Doc."""
    boundary = "df_boundary_x7z"
    meta = json.dumps({"name": filename, "mimeType": "application/vnd.google-apps.document",
                       "parents": [folder_id]})
    body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
            f"--{boundary}\r\nContent-Type: text/html\r\n\r\n").encode() + html_bytes + \
           f"\r\n--{boundary}--".encode()
    r = requests.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                      headers={"Authorization": f"Bearer {at}",
                               "Content-Type": f"multipart/related; boundary={boundary}"},
                      data=body)
    return r.json().get("id")


# ── Logo overlay ───────────────────────────────────────────────────────────────

def add_logo(src, dst):
    print("  Adding logo…")
    # PIL creates logo PNG (drawtext unavailable in static ffmpeg build)
    logo_path = dst + "_logo.png"
    lw, lh = 220, 42
    limg = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(limg)
    ldraw.rectangle([0, 0, lw - 1, lh - 1], fill=(0, 0, 0, 217))
    try:
        lfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except:
        lfont = ImageFont.load_default()
    ldraw.text((10, 8), "Digital Fusion", font=lfont, fill=(255, 255, 255, 255))
    limg.save(logo_path, "PNG")

    subprocess.run([
        FFMPEG, "-i", src, "-i", logo_path,
        "-filter_complex", "overlay=1050:668",
        "-c:a", "copy", "-y", dst
    ], check=True, capture_output=True)
    os.remove(logo_path)
    print(f"  Logo added: {os.path.getsize(dst)//1024//1024} MB")


# ── Gemini analysis ─────────────────────────────────────────────────────────────

GEMINI_PROMPT = """Watch this video carefully and return EXACTLY the following fields, separated by ━━━ lines.
No extra text before or after.

TITLE:
A punchy YouTube title (max 70 chars). No hashtags.

━━━

DESCRIPTION:
A full YouTube description (300-500 words). Include:
- Hook paragraph (2-3 sentences)
- 3-4 bullet points of key takeaways
- Timestamps/chapters section (estimate timestamps from the video content, format: 0:00 Intro)
- Call to action (Subscribe, leave a comment, hit the bell)
- Relevant hashtags at the end (5-8 hashtags)

━━━

TAGS:
Comma-separated YouTube tags (15-20 tags, no #)

━━━

THUMB_LINE1:
3-4 words for thumbnail (white text). Short, punchy, capitalised.

━━━

THUMB_LINE2:
3-4 words for thumbnail (red text). Completes the message.

━━━

LINKEDIN_DRAFT:
A LinkedIn post (~2500 characters). Rules:
- First line: bold post title with **
- No blank line between title and first paragraph
- Emojis ONLY at the very start of a line, never mid-sentence
- Blank lines between sections
- 4 sections: hook, what's happening, what it means for you, CTA with video URL placeholder [VIDEO_URL]
- No em-dashes, no AI waffle, human voice
- Bold section headers with **
"""

def gemini_analyse(video_path, gemini_key):
    print("  Uploading video to Gemini Files API…")
    size = os.path.getsize(video_path)
    # Start resumable upload
    r = requests.post(
        "https://generativelanguage.googleapis.com/upload/v1beta/files",
        headers={"X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                 "X-Goog-Upload-Header-Content-Length": str(size),
                 "X-Goog-Upload-Header-Content-Type": "video/mp4",
                 "Content-Type": "application/json"},
        params={"key": gemini_key},
        json={"file": {"display_name": os.path.basename(video_path)}}
    )
    upload_url = r.headers["X-Goog-Upload-URL"]
    with open(video_path, "rb") as f:
        data = f.read()
    r2 = requests.post(upload_url, headers={
        "Content-Length": str(size), "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize",
        "Content-Type": "video/mp4",
    }, data=data)
    file_uri = r2.json()["file"]["uri"]
    file_name = r2.json()["file"]["name"]
    print(f"  Gemini file: {file_name}")

    # Poll until ACTIVE
    for attempt in range(30):
        st = requests.get(f"https://generativelanguage.googleapis.com/v1beta/{file_name}",
                          params={"key": gemini_key}).json()
        state = st.get("state", "PROCESSING")
        if state == "ACTIVE":
            print("  Gemini file ACTIVE")
            break
        print(f"  Waiting for Gemini file… ({state})")
        time.sleep(10)
    else:
        raise RuntimeError("Gemini file never became ACTIVE")

    # Generate content
    print("  Generating SEO metadata + LinkedIn draft…")
    for attempt in range(3):
        r3 = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            params={"key": gemini_key},
            json={"contents": [{"parts": [
                {"text": GEMINI_PROMPT},
                {"file_data": {"mime_type": "video/mp4", "file_uri": file_uri}},
            ]}]},
            timeout=120
        )
        if r3.status_code == 200:
            return r3.json()["candidates"][0]["content"]["parts"][0]["text"]
        print(f"  Gemini attempt {attempt+1} failed: {r3.status_code}")
        time.sleep(5)
    raise RuntimeError("Gemini generation failed")


def parse_field(text, key):
    m = re.search(rf'^{key}:\s*(.+?)(?=\n━|\Z)', text, re.M | re.S)
    return m.group(1).strip() if m else ""


# ── Thumbnail ──────────────────────────────────────────────────────────────────

def make_thumbnail(video_path, line1, line2, out_path):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([
            FFMPEG, "-i", video_path, "-vf", "fps=1/30",
            "-q:v", "2", os.path.join(tmp, "frame_%03d.jpg"), "-y"
        ], check=True, capture_output=True)
        frames = sorted(f for f in os.listdir(tmp) if f.startswith("frame_"))
        pick = max(0, len(frames) // 3)
        bg_path = os.path.join(tmp, frames[pick])

        W, H = 1280, 720
        img = Image.open(bg_path).convert("RGB").resize((W, H), Image.LANCZOS)
        img = ImageEnhance.Brightness(img).enhance(0.75)

        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_o = ImageDraw.Draw(overlay)
        for x in range(700):
            alpha = int(150 * (1 - x / 700) ** 0.6)
            draw_o.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        try:
            font_big  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
            font_chan = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            font_big = font_chan = ImageFont.load_default()

        x0, y0 = 60, H // 2 - 130
        draw.text((x0+3, y0+3), line1, font=font_big, fill=(0, 0, 0))
        draw.text((x0, y0), line1, font=font_big, fill=(255, 255, 255))
        y2 = y0 + 120
        draw.text((x0+3, y2+3), line2, font=font_big, fill=(0, 0, 0))
        draw.text((x0, y2), line2, font=font_big, fill=(220, 30, 30))

        pad = 14
        bbox = draw.textbbox((0, 0), "Digital Fusion", font=font_chan)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.rectangle([20, 20, 20+tw+pad*2, 20+th+pad], fill=(20, 20, 20, 220))
        draw.text((20+pad, 20+pad//2), "Digital Fusion", font=font_chan, fill=(255, 255, 255))
        draw.rectangle([0, 0, 8, H], fill=(220, 30, 30))

        img.save(out_path, "JPEG", quality=95)
    print(f"  Thumbnail saved: {os.path.getsize(out_path)//1024} KB")


# ── YouTube ────────────────────────────────────────────────────────────────────

def youtube_upload(video_path, title, description, tags, publish_at, at):
    print(f"  Uploading to YouTube… (scheduled {publish_at})")
    size = os.path.getsize(video_path)
    meta = {
        "snippet": {"title": title, "description": description,
                    "tags": [t.strip() for t in tags.split(",")],
                    "categoryId": "28", "defaultLanguage": "en-GB", "defaultAudioLanguage": "en-GB"},
        "status": {"privacyStatus": "private", "publishAt": publish_at,
                   "selfDeclaredMadeForKids": False}
    }
    r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {at}", "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
        json=meta)
    upload_url = r.headers["Location"]
    chunk_size = 8 * 1024 * 1024
    uploaded = 0
    yt_id = None
    with open(video_path, "rb") as f:
        while uploaded < size:
            chunk = f.read(chunk_size)
            r2 = requests.put(upload_url, data=chunk, headers={
                "Content-Type": "video/mp4", "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {uploaded}-{uploaded+len(chunk)-1}/{size}"})
            uploaded += len(chunk)
            pct = round(uploaded / size * 100)
            if pct % 20 == 0:
                print(f"  {pct}%", flush=True)
            if r2.status_code in (200, 201):
                yt_id = r2.json()["id"]
                print(f"  ✓ YouTube ID: {yt_id}")
    return yt_id

def youtube_set_thumbnail(thumb_path, yt_id, at):
    with open(thumb_path, "rb") as f:
        data = f.read()
    r = requests.post(
        f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={yt_id}&uploadType=media",
        headers={"Authorization": f"Bearer {at}", "Content-Type": "image/jpeg"}, data=data)
    print(f"  Thumbnail → YouTube: {'✓' if r.status_code == 200 else f'ERR {r.status_code}'}")


# ── LinkedIn doc ───────────────────────────────────────────────────────────────

def linkedin_to_html(text):
    lines = text.strip().split('\n')
    parts = ['<html><body style="font-family:Arial,sans-serif;font-size:11pt;line-height:1.7;max-width:640px;">']
    for line in lines:
        s = line.strip()
        if not s:
            parts.append('<p>&nbsp;</p>')
        else:
            converted = BOLD_RE.sub(r'<b>\1</b>', s)
            parts.append(f'<p>{converted}</p>')
    parts.append('</body></html>')
    return '\n'.join(parts)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 df_pipeline.py <drive_file_id> <original_filename>")
        sys.exit(1)

    drive_file_id = sys.argv[1]
    original_name = sys.argv[2]

    tok = load_tokens()
    at = get_access_token(tok)
    gemini_key = tok["gemini_api_key"]
    publish_at = next_thursday_6pm_bst()
    print(f"\n=== Digital Fusion Pipeline ===")
    print(f"File: {original_name}")
    print(f"Scheduled: {publish_at}\n")

    with tempfile.TemporaryDirectory() as tmp:
        original_path  = os.path.join(tmp, "original.mp4")
        processed_path = os.path.join(tmp, "processed.mp4")
        thumb_path     = os.path.join(tmp, "thumbnail.jpg")

        # 1. Download
        print("[ 1/7 ] Downloading video…")
        drive_download(drive_file_id, original_path, at)

        # 2. Logo overlay
        print("[ 2/7 ] Adding logo…")
        add_logo(original_path, processed_path)

        # 3. Gemini analysis
        print("[ 3/7 ] Gemini transcription + SEO…")
        raw = gemini_analyse(original_path, gemini_key)
        print("\n--- Gemini raw output ---")
        print(raw[:800])
        print("…\n")

        title      = parse_field(raw, "TITLE")
        desc       = parse_field(raw, "DESCRIPTION")
        tags       = parse_field(raw, "TAGS")
        thumb_l1   = parse_field(raw, "THUMB_LINE1")
        thumb_l2   = parse_field(raw, "THUMB_LINE2")
        linkedin   = parse_field(raw, "LINKEDIN_DRAFT")

        print(f"Title:       {title}")
        print(f"Thumb L1:    {thumb_l1}")
        print(f"Thumb L2:    {thumb_l2}")
        print(f"Tags:        {tags[:80]}…")
        print(f"LinkedIn:    {len(linkedin)} chars\n")

        # 4. Thumbnail
        print("[ 4/7 ] Generating thumbnail…")
        make_thumbnail(original_path, thumb_l1, thumb_l2, thumb_path)

        # 5. Create Drive episode folder
        print("[ 5/7 ] Creating episode folder in Drive…")
        ep_folder = drive_create_folder(title, PROCESSED_FOLDER_ID, at)
        print(f"  Episode folder: {ep_folder}")

        # 6. YouTube upload
        print("[ 6/7 ] Uploading to YouTube…")
        yt_id = youtube_upload(processed_path, title, desc, tags, publish_at, at)
        youtube_set_thumbnail(thumb_path, yt_id, at)
        yt_url = f"https://www.youtube.com/watch?v={yt_id}"

        # 7. Drive: save files + LinkedIn doc
        print("[ 7/7 ] Saving assets to Drive…")
        drive_upload(original_path,  f"{original_name}",  ep_folder, at)
        drive_upload(processed_path, original_name.replace(".mp4", "_processed.mp4"), ep_folder, at)
        drive_upload(thumb_path, "thumbnail.jpg", ep_folder, at, mime="image/jpeg")

        li_text = linkedin.replace("[VIDEO_URL]", yt_url)
        li_html = linkedin_to_html(li_text).encode("utf-8")
        doc_id = drive_upload_doc(li_html, "linkedin_draft", ep_folder, at)
        print(f"  LinkedIn doc: https://docs.google.com/document/d/{doc_id}/edit")

    print(f"\n✓ Pipeline complete!")
    print(f"  YouTube:  {yt_url}")
    print(f"  Drive folder: https://drive.google.com/drive/folders/{ep_folder}")
    print(f"  Scheduled: {publish_at}")


if __name__ == "__main__":
    main()
