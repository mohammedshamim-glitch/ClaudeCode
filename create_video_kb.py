#!/usr/bin/env python3
"""
Monkey Finance Video Creator — Ken Burns Edition
Same as create_video.py but applies slow zoom/pan (Ken Burns) to each image.
Each scene gets a different effect, cycling through 6 styles.
"""

import csv, io, json, os, re, sys, subprocess, tempfile, shutil, requests
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
    files, page_token = [], None
    while True:
        params = {
            "q": f"'{folder_id}' in parents" + (f" and mimeType contains '{mime_filter}'" if mime_filter else ""),
            "fields": "nextPageToken,files(id,name,mimeType,modifiedTime)",
            "pageSize": 100,
        }
        if page_token:
            params["pageToken"] = page_token
        r = requests.get(
            "https://www.googleapis.com/drive/v3/files",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        r.raise_for_status()
        data = r.json()
        files.extend(data.get("files", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return files

def drive_load_csv(token, file_id):
    """Download a CSV file and return rows as list of dicts."""
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.content.decode("utf-8")))
    return list(reader)

def drive_download_file(token, file_id, local_path):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"}, stream=True
    )
    r.raise_for_status()
    with open(local_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

def drive_delete_existing(token, filename, folder_id):
    """Delete any existing files with this name in the folder before uploading."""
    r = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": f"'{folder_id}' in parents and name='{filename}' and trashed=false",
            "fields": "files(id,name)",
        },
    )
    r.raise_for_status()
    for f in r.json().get("files", []):
        requests.delete(
            f"https://www.googleapis.com/drive/v3/files/{f['id']}",
            headers={"Authorization": f"Bearer {token}"},
        ).raise_for_status()
        print(f"  ✓ Deleted existing {f['name']}")

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
KB_SCALE = 1.2   # zoom factor — keep low (1.15–1.25) to avoid cropping text

EFFECT_NAMES = [
    "pan left → right",
    "pan right → left",
    "pan top → bottom",
    "pan bottom → top",
]

def get_kb_filter(idx, duration, w, h):
    """
    Returns a smooth Ken Burns vf filter string using scale+crop+t.
    Image is pre-scaled to KB_SCALE× output, then a time-varying crop
    window pans across it, then rescaled to w×h.
    't' is ffmpeg's built-in time variable (seconds, continuous).
    idx selects one of 4 effects.
    """
    D   = duration
    LW  = int(w * KB_SCALE)
    LH  = int(h * KB_SCALE)
    px  = LW - w
    py  = LH - h
    cx  = px // 2
    cy  = py // 2

    P = f"min(t/{D:.6f},1)"

    effects = [
        # 0. Pan left → right
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=white,"
         f"crop=w={w}:h={h}:x='{px}*{P}':y={cy},"
         f"scale={w}:{h},setsar=1"),

        # 1. Pan right → left
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=white,"
         f"crop=w={w}:h={h}:x='{px}*(1-{P})':y={cy},"
         f"scale={w}:{h},setsar=1"),

        # 2. Pan top → bottom
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=white,"
         f"crop=w={w}:h={h}:x={cx}:y='{py}*{P}',"
         f"scale={w}:{h},setsar=1"),

        # 3. Pan bottom → top
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=white,"
         f"crop=w={w}:h={h}:x={cx}:y='{py}*(1-{P})',"
         f"scale={w}:{h},setsar=1"),
    ]
    return effects[idx % len(effects)]


def movement_to_effect_idx(text):
    """
    Maps a KB label from 05-kb-movements.txt to one of the 4 effect indices:
      0 = pan left to right
      1 = pan right to left
      2 = pan top to bottom
      3 = pan bottom to top
    Returns None for unrecognised text (old-format descriptions) so the
    caller can fall back to cycling.
    """
    t = text.strip().lower()
    if t == "pan left to right":
        return 0
    if t == "pan right to left":
        return 1
    if t == "pan top to bottom":
        return 2
    if t == "pan bottom to top":
        return 3
    return None


def load_kb_movements(local_path):
    """
    Parses 05-kb-movements.txt into an ordered list of (scene_id, movement_text).
    Format: blank-line separated blocks, each starting with a scene number.
    """
    with open(local_path, encoding="utf-8") as f:
        content = f.read()
    movements = []
    for block in content.strip().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        parts = block.split(" ", 1)
        scene_id = parts[0]
        text = parts[1].strip() if len(parts) > 1 else ""
        movements.append((scene_id, text))
    return movements

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

def create_video_kb(image_paths, audio_path, output_path, durations=None, use_kb=True, kb_movements=None):
    w, h           = RESOLUTION_W, RESOLUTION_H
    total_duration = get_audio_duration(audio_path)
    n              = len(image_paths)

    if durations is None:
        durations = [total_duration / n] * n
        print(f"  Timing          : equal split (no auto_timings.csv found)")
    else:
        print(f"  Timing          : from auto_timings.csv")

    kb_source = "off"
    if use_kb:
        kb_source = f"05-kb-movements.txt ({len(kb_movements)} entries)" if kb_movements else "cycling (no kb file found)"
    print(f"  Ken Burns       : {kb_source}")
    print(f"  Audio duration  : {total_duration:.2f}s")
    print(f"  Images          : {n}")
    print(f"  Duration range  : {min(durations):.2f}s – {max(durations):.2f}s per scene")

    tmpdir = os.path.dirname(output_path)
    segments = []

    static_vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    )
    kb_cycle_idx = 0

    for i, img in enumerate(image_paths):
        seg = os.path.join(tmpdir, f"seg_{i:03d}.mp4")
        dur = durations[i]
        if use_kb and i % 4 == 0:
            if kb_movements and i < len(kb_movements):
                scene_id, movement_text = kb_movements[i]
                effect_idx = movement_to_effect_idx(movement_text)
                if effect_idx is None:
                    # Old-format description — cycle through the 4 effects
                    effect_idx = kb_cycle_idx % 4
                    kb_cycle_idx += 1
                label = f"{EFFECT_NAMES[effect_idx]} [{scene_id}]"
            else:
                effect_idx = kb_cycle_idx % 4
                label = f"{EFFECT_NAMES[effect_idx]} [cycle]"
                kb_cycle_idx += 1
            vf = get_kb_filter(effect_idx, dur, w, h)
            print(f"  Scene {i+1}/{n}: {dur:.2f}s  {label}")
        else:
            vf = static_vf
        create_segment(img, seg, dur, vf, w, h)
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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if not args:
        print("Usage: python3 create_video_kb.py <episode_folder_id> [output_filename] [--no-kb]")
        print("  --no-kb   Render all scenes as static (no Ken Burns effects)")
        sys.exit(1)

    folder_id  = args[0]
    use_kb     = "--no-kb" not in flags

    print("Authenticating with Google Drive...")
    token = get_access_token()
    print("  ✓ Authenticated")

    # Use folder name as video filename (or override from argv)
    if len(args) > 1:
        out_name = args[1]
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

    # List and sort images by modification time (original upload order)
    print("Listing images...")
    image_files = drive_list_files(token, images_folder["id"], mime_filter="image/")
    image_files = [f for f in image_files if f["mimeType"].startswith("image/")]
    image_files.sort(key=lambda x: x["modifiedTime"])
    if not image_files:
        print("ERROR: No images found.")
        sys.exit(1)
    print(f"  ✓ {len(image_files)} images (sorted by modification time)")

    # Find narration.mp3, optional auto_timings.csv, optional 05-kb-movements.txt
    print("Finding narration.mp3...")
    all_files = drive_list_files(token, folder_id)
    audio_file   = next((f for f in all_files if f["name"] == "narration.mp3"), None)
    timings_file = (
        next((f for f in all_files if f["name"] == "audio_timings_new.csv"), None) or
        next((f for f in all_files if f["name"] == "auto_timings.csv"), None)
    )
    kb_file      = next((f for f in all_files if f["name"] == "05-kb-movements.txt"), None)
    if not audio_file:
        print("ERROR: narration.mp3 not found.")
        sys.exit(1)
    print(f"  ✓ Found narration.mp3")
    if timings_file:
        print(f"  ✓ Found {timings_file['name']} — will use per-scene durations")
    else:
        print(f"  ⚠ No timings CSV found — falling back to equal splits")
        print(f"    Run generate_timings_whisper.py first for accurate scene durations")
    if kb_file:
        print(f"  ✓ Found 05-kb-movements.txt — KB effects will follow the file")
    else:
        print(f"  ⚠ 05-kb-movements.txt not found — KB effects will cycle automatically")

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

        # Load per-scene durations from CSV if available
        durations = None
        if timings_file:
            rows = drive_load_csv(token, timings_file["id"])
            rows.sort(key=lambda r: int(r["scene"]))
            if len(rows) == len(image_paths):
                durations = [float(r["duration_seconds"]) for r in rows]
            else:
                print(f"  ⚠ CSV has {len(rows)} rows but {len(image_paths)} images — using equal splits")

        # Load KB movements from file if available
        kb_movements = None
        if kb_file:
            local_kb = os.path.join(tmpdir, "05-kb-movements.txt")
            drive_download_file(token, kb_file["id"], local_kb)
            kb_movements = load_kb_movements(local_kb)
            print(f"  ✓ Loaded {len(kb_movements)} KB movement entries")
            if len(kb_movements) != len(image_paths):
                print(f"  ⚠ KB file has {len(kb_movements)} entries but {len(image_paths)} images — index mismatch possible")

        mode = "Ken Burns" if use_kb else "static (no Ken Burns)"
        print(f"\nRendering video ({RESOLUTION_W}x{RESOLUTION_H} @ {FPS}fps) — {mode}...")
        create_video_kb(image_paths, audio_path, OUTPUT_VIDEO, durations, use_kb, kb_movements)
        size_mb = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
        print(f"  ✓ Video created ({size_mb:.1f} MB)")

        print(f"\nUploading {out_name} to Drive...")
        token = get_access_token()
        drive_delete_existing(token, out_name, folder_id)
        result = drive_upload(token, OUTPUT_VIDEO, out_name, folder_id)
        print(f"  ✓ Uploaded: {result['name']}")
        print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
