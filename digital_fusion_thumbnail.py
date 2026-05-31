#!/usr/bin/env python3
"""
Digital Fusion — Thumbnail Generator
Extracts best frame from video, overlays bold text in ColdFusion style, uploads to YouTube + Drive.
Usage: python3 digital_fusion_thumbnail.py <video_path> <line1> <line2_red> <video_id> <drive_folder_id>
"""

import sys, os, requests, json, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

TOKEN_FILE = "/home/user/ClaudeCode/token.json"


def load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)


def refresh_access_token(tokens):
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":     tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "refresh_token": tokens["digital_fusion_refresh_token"],
        "grant_type":    "refresh_token",
    })
    return r.json()["access_token"]


def extract_best_frame(video_path, out_dir):
    subprocess.run([
        "ffmpeg", "-i", video_path, "-vf", "fps=1/30",
        "-q:v", "2", os.path.join(out_dir, "frame_%03d.jpg"), "-y"
    ], check=True, capture_output=True)
    frames = sorted([f for f in os.listdir(out_dir) if f.startswith("frame_")])
    # Pick frame at ~30% through the video
    pick = max(0, len(frames) // 3)
    return os.path.join(out_dir, frames[pick])


def make_thumbnail(bg_path, out_path, line1, line2_red, channel="Digital Fusion"):
    W, H = 1280, 720
    img = Image.open(bg_path).convert("RGB").resize((W, H), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.75)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_o = ImageDraw.Draw(overlay)
    text_width = 680
    for x in range(text_width):
        alpha = int(140 * (1 - x / text_width) ** 0.6)
        draw_o.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    try:
        font_big  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_chan = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        font_big = font_chan = ImageFont.load_default()

    x_text, y_start = 60, H // 2 - 130

    # Line 1 — white
    draw.text((x_text+4, y_start+4), line1, font=font_big, fill=(0, 0, 0))
    draw.text((x_text, y_start), line1, font=font_big, fill=(255, 255, 255))

    # Line 2 — red
    y2 = y_start + 120
    draw.text((x_text+4, y2+4), line2_red, font=font_big, fill=(0, 0, 0))
    draw.text((x_text, y2), line2_red, font=font_big, fill=(220, 30, 30))

    # Channel branding
    pad = 14
    bbox = draw.textbbox((0, 0), channel, font=font_chan)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.rectangle([20, 20, 20+tw+pad*2, 20+th+pad], fill=(20, 20, 20, 220))
    draw.text((20+pad, 20+pad//2), channel, font=font_chan, fill=(255, 255, 255))

    # Red left accent bar
    draw.rectangle([0, 0, 8, H], fill=(220, 30, 30))

    img.save(out_path, "JPEG", quality=95)
    print(f"  Thumbnail saved: {out_path}")


def upload_thumbnail_youtube(thumb_path, video_id, access_token):
    with open(thumb_path, "rb") as f:
        data = f.read()
    r = requests.post(
        f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}&uploadType=media",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "image/jpeg"},
        data=data
    )
    print(f"  YouTube thumbnail: {'✓' if r.status_code == 200 else f'ERROR {r.status_code}'}")


def upload_thumbnail_drive(thumb_path, folder_id, access_token):
    with open(thumb_path, "rb") as f:
        data = f.read()
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json",
                 "X-Upload-Content-Type": "image/jpeg", "X-Upload-Content-Length": str(len(data))},
        json={"name": "thumbnail.jpg", "parents": [folder_id]}
    )
    r2 = requests.put(r.headers["Location"],
        headers={"Content-Type": "image/jpeg", "Content-Length": str(len(data))}, data=data)
    print(f"  Drive thumbnail: {'✓' if r2.status_code in (200,201) else f'ERROR {r2.status_code}'}")


def main():
    if len(sys.argv) < 6:
        print("Usage: python3 digital_fusion_thumbnail.py <video_path> <line1> <line2_red> <yt_video_id> <drive_folder_id>")
        sys.exit(1)

    video_path, line1, line2_red, video_id, folder_id = sys.argv[1:6]

    tokens = load_tokens()
    access_token = refresh_access_token(tokens)

    with tempfile.TemporaryDirectory() as tmp:
        frame = extract_best_frame(video_path, tmp)
        thumb = os.path.join(tmp, "thumbnail.jpg")
        make_thumbnail(frame, thumb, line1, line2_red)
        upload_thumbnail_youtube(thumb, video_id, access_token)
        upload_thumbnail_drive(thumb, folder_id, access_token)

    print("✓ Thumbnail done!")


if __name__ == "__main__":
    main()
