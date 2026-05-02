#!/usr/bin/env python3
"""
Monkey Finance Video Creator
1. Finds images (in /images subfolder) and narration.mp3 in a Drive episode folder
2. Downloads them locally
3. Calculates equal duration per image based on audio length
4. Creates 1920x1080 MP4 with ffmpeg
5. Uploads video.mp4 back to the episode folder on Drive
"""

import json, os, sys, re, time, subprocess, tempfile, shutil, requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN_FILE       = "/home/user/ClaudeCode/token.json"
OUTPUT_VIDEO     = "/home/user/ClaudeCode/video.mp4"
RESOLUTION_W     = 1920
RESOLUTION_H     = 1080
VIDEO_CRF        = 23       # H.264 quality (lower = better, 18-28 is typical)
AUDIO_BITRATE    = "192k"
OUTPUT_FILENAME  = "video.mp4"

# ── OAuth2 (shared with run_tts.py) ──────────────────────────────────────────
def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        print("ERROR: token.json not found. Run setup_auth.py first.")
        sys.exit(1)
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

def get_access_token():
    tokens = load_tokens()
    if "access_token" in tokens:
        r = requests.get(
            "https://www.googleapis.com/oauth2/v1/tokeninfo",
            params={"access_token": tokens["access_token"]}
        )
        if r.ok and r.json().get("expires_in", 0) > 60:
            return tokens["access_token"]
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":     tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "refresh_token": tokens["refresh_token"],
        "grant_type":    "refresh_token",
    })
    if not r.ok:
        print(f"ERROR refreshing token: {r.text}")
        sys.exit(1)
    tokens["access_token"] = r.json()["access_token"]
    save_tokens(tokens)
    return tokens["access_token"]

# ── Google Drive helpers ──────────────────────────────────────────────────────
def drive_list_files(token, folder_id, mime_filter=None):
    query = f"'{folder_id}' in parents"
    if mime_filter:
        query += f" and mimeType contains '{mime_filter}'"
    r = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": query,
            "fields": "files(id,name,mimeType,modifiedTime)",
            "pageSize": 100,
        }
    )
    r.raise_for_status()
    return r.json().get("files", [])

def drive_download_file(token, file_id, local_path):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"},
        stream=True
    )
    r.raise_for_status()
    with open(local_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

def drive_upload(token, local_path, filename, folder_id, mime="video/mp4"):
    with open(local_path, "rb") as f:
        data = f.read()
    metadata = json.dumps({"name": filename, "parents": [folder_id]}).encode()
    boundary = b"video_boundary_xyz"
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n" +
        metadata + b"\r\n"
        b"--" + boundary + b"\r\n" +
        f"Content-Type: {mime}\r\n\r\n".encode() +
        data + b"\r\n"
        b"--" + boundary + b"--"
    )
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary.decode()}",
        },
        data=body,
    )
    if not r.ok:
        print(f"  Drive upload error {r.status_code}: {r.text}")
    r.raise_for_status()
    return r.json()

# ── Audio / Video helpers ─────────────────────────────────────────────────────
def get_audio_duration(audio_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())

def create_video(image_paths, audio_path, output_path):
    duration   = get_audio_duration(audio_path)
    num_images = len(image_paths)
    per_image  = duration / num_images

    print(f"  Audio duration : {duration:.2f}s")
    print(f"  Images         : {num_images}")
    print(f"  Per image      : {per_image:.2f}s")

    # Build ffconcat file
    concat_path = output_path.replace(".mp4", "_concat.txt")
    with open(concat_path, "w") as f:
        f.write("ffconcat version 1.0\n")
        for img in image_paths:
            f.write(f"file '{img}'\n")
            f.write(f"duration {per_image:.6f}\n")
        # Repeat last frame — required by concat demuxer to set correct end pts
        f.write(f"file '{image_paths[-1]}'\n")

    w, h = RESOLUTION_W, RESOLUTION_H
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_path,
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", str(VIDEO_CRF),
        "-vf", vf,
        "-c:a", "aac", "-b:a", AUDIO_BITRATE,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-shortest",
        output_path
    ]

    print("  Running ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error:\n{result.stderr[-2000:]}")
        sys.exit(1)

    os.unlink(concat_path)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 create_video.py <episode_folder_id> [output_filename]")
        print("Example: python3 create_video.py 1Fi6ozVLcf3yW0tCxMEOdn5wOiSVPZhT6 video.mp4")
        sys.exit(1)

    folder_id   = sys.argv[1]
    out_name    = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILENAME

    print("Authenticating with Google Drive...")
    token = get_access_token()
    print("  ✓ Authenticated")

    # Find images subfolder
    print("Finding images subfolder...")
    subfolders = drive_list_files(token, folder_id)
    images_folder = next((f for f in subfolders if f["name"].lower() == "images" and "folder" in f["mimeType"]), None)
    if not images_folder:
        print("ERROR: No 'images' subfolder found in the episode folder.")
        sys.exit(1)
    images_folder_id = images_folder["id"]
    print(f"  ✓ Found images folder: {images_folder_id}")

    # List images sorted by modifiedTime (scene order)
    print("Listing images...")
    image_files = drive_list_files(token, images_folder_id, mime_filter="image/")
    image_files = [f for f in image_files if f["mimeType"].startswith("image/")]
    image_files.sort(key=lambda x: x["modifiedTime"])
    if not image_files:
        print("ERROR: No images found in the images folder.")
        sys.exit(1)
    print(f"  ✓ Found {len(image_files)} images (sorted by modification time)")
    for i, img in enumerate(image_files, 1):
        print(f"    {i}. {img['name']} ({img['modifiedTime']})")

    # Find narration.mp3
    print("Finding narration.mp3...")
    all_files = drive_list_files(token, folder_id)
    audio_file = next((f for f in all_files if f["name"] == "narration.mp3"), None)
    if not audio_file:
        print("ERROR: narration.mp3 not found in episode folder.")
        sys.exit(1)
    print(f"  ✓ Found {audio_file['name']}")

    # Download everything to a temp directory
    tmpdir = tempfile.mkdtemp(prefix="mf_video_")
    try:
        print(f"\nDownloading files to {tmpdir}...")
        audio_path = os.path.join(tmpdir, "narration.mp3")
        drive_download_file(token, audio_file["id"], audio_path)
        print(f"  ✓ narration.mp3")

        image_paths = []
        for i, img in enumerate(image_files):
            ext = os.path.splitext(img["name"])[1] or ".jpg"
            local = os.path.join(tmpdir, f"scene_{i+1:03d}{ext}")
            drive_download_file(token, img["id"], local)
            image_paths.append(local)
            print(f"  ✓ scene_{i+1:03d}{ext}")

        # Create video
        print(f"\nCreating {RESOLUTION_W}x{RESOLUTION_H} video...")
        create_video(image_paths, audio_path, OUTPUT_VIDEO)
        size_mb = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
        print(f"  ✓ Video created ({size_mb:.1f} MB)")

        # Upload to Drive
        print(f"\nUploading {out_name} to Drive...")
        token = get_access_token()
        result = drive_upload(token, OUTPUT_VIDEO, out_name, folder_id)
        print(f"  ✓ Uploaded: {result['name']}")
        print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
