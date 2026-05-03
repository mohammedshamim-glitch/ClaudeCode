#!/usr/bin/env python3
"""
Monkey Finance Video Creator — Ken Burns Edition
Same as create_video.py but applies slow zoom/pan (Ken Burns) to each image.
Each scene gets a different effect, cycling through 6 styles.
"""

import json, os, sys, time, subprocess, tempfile, shutil, requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN_FILE      = "/home/user/ClaudeCode/token.json"
OUTPUT_VIDEO    = "/home/user/ClaudeCode/video_kb.mp4"
RESOLUTION_W    = 1920
RESOLUTION_H    = 1080
FPS             = 30
VIDEO_CRF       = 23
AUDIO_BITRATE   = "192k"
OUTPUT_FILENAME = "video_kb.mp4"

# ── OAuth2 (shared) ───────────────────────────────────────────────────────────
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
def drive_get_name(token, file_id):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"fields": "name"}
    )
    r.raise_for_status()
    return r.json()["name"]

def drive_list_files(token, folder_id, mime_filter=None):
    query = f"'{folder_id}' in parents"
    if mime_filter:
        query += f" and mimeType contains '{mime_filter}'"
    r = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "fields": "files(id,name,mimeType,modifiedTime)", "pageSize": 100}
    )
    r.raise_for_status()
    return r.json().get("files", [])

def drive_download_file(token, file_id, local_path):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"}, stream=True
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

# ── Ken Burns effects ─────────────────────────────────────────────────────────
def get_kb_filter(idx, duration, w, h):
    """
    Returns a smooth Ken Burns vf filter string using scale+crop+t.
    The image is pre-scaled to 1.5× output (LW x LH), then a time-varying
    crop window slides/zooms into it, then rescaled to w×h.
    't' is ffmpeg's built-in time variable (seconds, continuous).
    Cycles through 6 styles.
    """
    D   = duration          # segment duration in seconds
    LW  = int(w * 1.5)     # 2880 for 1920-wide output
    LH  = int(h * 1.5)     # 1620 for 1080-high output
    # padding from large to crop-out (pixels available to shift)
    px  = LW - w            # 960
    py  = LH - h            # 540
    cx  = px // 2           # 480  (centre offset)
    cy  = py // 2           # 270

    # progress expression clamped to [0,1]
    P = f"min(t/{D:.6f},1)"

    effects = [
        # 1. Zoom in to centre: crop shrinks from full large → output size
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=black,"
         f"crop=w='{LW}-{px}*{P}':h='{LH}-{py}*{P}'"
         f":x='{cx}*{P}':y='{cy}*{P}',"
         f"scale={w}:{h},setsar=1"),

        # 2. Pan left → right at 1.5× zoom
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=black,"
         f"crop=w={w}:h={h}:x='{px}*{P}':y={cy},"
         f"scale={w}:{h},setsar=1"),

        # 3. Pan right → left at 1.5× zoom
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=black,"
         f"crop=w={w}:h={h}:x='{px}*(1-{P})':y={cy},"
         f"scale={w}:{h},setsar=1"),

        # 4. Zoom out from centre: crop grows from output size → full large
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=black,"
         f"crop=w='{w}+{px}*{P}':h='{h}+{py}*{P}'"
         f":x='{cx}*(1-{P})':y='{cy}*(1-{P})',"
         f"scale={w}:{h},setsar=1"),

    ]
    return effects[idx % len(effects)]

# ── Audio helpers ─────────────────────────────────────────────────────────────
def get_audio_duration(audio_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())

# ── Video creation ────────────────────────────────────────────────────────────
def create_segment(image_path, segment_path, duration, vf, w, h):
    """Render one image into a video segment with Ken Burns effect."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(FPS), "-i", image_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-t", f"{duration:.6f}",
        segment_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error on {os.path.basename(image_path)}:\n{result.stderr[-1000:]}")
        sys.exit(1)

def create_video_kb(image_paths, audio_path, output_path):
    w, h     = RESOLUTION_W, RESOLUTION_H
    duration = get_audio_duration(audio_path)
    n        = len(image_paths)
    per_img  = duration / n

    print(f"  Audio duration  : {duration:.2f}s")
    print(f"  Images          : {n}")
    print(f"  Per image       : {per_img:.2f}s ({int(per_img * FPS)} frames at {FPS}fps)")

    tmpdir = os.path.dirname(output_path)
    segments = []

    effect_names = [
        "zoom in → centre", "pan left → right", "pan right → left",
        "zoom out ← centre",
    ]
    static_vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    )
    kb_idx = 0  # counter for cycling KB effect styles

    for i, img in enumerate(image_paths):
        seg = os.path.join(tmpdir, f"seg_{i:03d}.mp4")
        if i % 4 == 0:
            vf = get_kb_filter(kb_idx, per_img, w, h)
            print(f"  Scene {i+1}/{n}: {effect_names[kb_idx % 6]} [Ken Burns]")
            kb_idx += 1
        else:
            vf = static_vf
            print(f"  Scene {i+1}/{n}: static")
        create_segment(img, seg, per_img, vf, w, h)
        segments.append(seg)

    # Concatenate segments (copy, no re-encode)
    concat_file = os.path.join(tmpdir, "concat.txt")
    with open(concat_file, "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    merged = os.path.join(tmpdir, "merged.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
         "-c:v", "copy", merged],
        capture_output=True, check=True
    )

    # Mux with audio
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", merged, "-i", audio_path,
         "-c:v", "copy", "-c:a", "aac", "-b:a", AUDIO_BITRATE,
         "-movflags", "+faststart", "-shortest", output_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  Mux error:\n{result.stderr[-1000:]}")
        sys.exit(1)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 create_video_kb.py <episode_folder_id> [output_filename]")
        print("Example: python3 create_video_kb.py 1Fi6ozVLcf3yW0tCxMEOdn5wOiSVPZhT6 video_kb.mp4")
        sys.exit(1)

    folder_id = sys.argv[1]

    print("Authenticating with Google Drive...")
    token = get_access_token()
    print("  ✓ Authenticated")

    # Use folder name as video filename (or override from argv)
    if len(sys.argv) > 2:
        out_name = sys.argv[2]
    else:
        folder_name = drive_get_name(token, folder_id)
        out_name = f"{folder_name}.mp4"
    print(f"  Output filename : {out_name}")

    # Find images subfolder
    print("Finding images subfolder...")
    subfolders = drive_list_files(token, folder_id)
    images_folder = next((f for f in subfolders if f["name"].lower() == "images" and "folder" in f["mimeType"]), None)
    if not images_folder:
        print("ERROR: No 'images' subfolder found.")
        sys.exit(1)
    print(f"  ✓ Found: {images_folder['id']}")

    # List and sort images by modification time
    print("Listing images...")
    image_files = drive_list_files(token, images_folder["id"], mime_filter="image/")
    image_files = [f for f in image_files if f["mimeType"].startswith("image/")]
    image_files.sort(key=lambda x: x["modifiedTime"])
    if not image_files:
        print("ERROR: No images found.")
        sys.exit(1)
    print(f"  ✓ {len(image_files)} images (sorted by modification time)")

    # Find narration.mp3
    print("Finding narration.mp3...")
    all_files = drive_list_files(token, folder_id)
    audio_file = next((f for f in all_files if f["name"] == "narration.mp3"), None)
    if not audio_file:
        print("ERROR: narration.mp3 not found.")
        sys.exit(1)
    print(f"  ✓ Found narration.mp3")

    # Download to temp dir
    tmpdir = tempfile.mkdtemp(prefix="mf_kb_")
    try:
        print(f"\nDownloading to {tmpdir}...")
        audio_path = os.path.join(tmpdir, "narration.mp3")
        drive_download_file(token, audio_file["id"], audio_path)
        print("  ✓ narration.mp3")

        image_paths = []
        for i, img in enumerate(image_files):
            ext = os.path.splitext(img["name"])[1] or ".jpg"
            local = os.path.join(tmpdir, f"scene_{i+1:03d}{ext}")
            drive_download_file(token, img["id"], local)
            image_paths.append(local)
            print(f"  ✓ scene_{i+1:03d}{ext}")

        print(f"\nRendering Ken Burns video ({RESOLUTION_W}x{RESOLUTION_H} @ {FPS}fps)...")
        create_video_kb(image_paths, audio_path, OUTPUT_VIDEO)
        size_mb = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
        print(f"  ✓ Video created ({size_mb:.1f} MB)")

        print(f"\nUploading {out_name} to Drive...")
        token = get_access_token()
        result = drive_upload(token, OUTPUT_VIDEO, out_name, folder_id)
        print(f"  ✓ Uploaded: {result['name']}")
        print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
