#!/usr/bin/env python3
"""
Merge AI-generated video clips into a final episode MP4 with audio.

For each scene:
  - clip duration < scene duration → slow down (setpts) to fill the scene
  - clip duration >= scene duration → trim to scene duration at 1.0x speed

Usage:
    python3 create_video_from_clips.py <episode_folder_id> [output_filename]
"""

import json, requests, os, csv, subprocess, sys, re, shutil

TOKEN_FILE = "/home/user/ClaudeCode/token.json"
WORK_DIR   = "/tmp/clip_render"


def get_access_token():
    tokens = json.load(open(TOKEN_FILE))
    r = requests.get("https://www.googleapis.com/oauth2/v1/tokeninfo",
                     params={"access_token": tokens.get("access_token", "")})
    if r.ok and r.json().get("expires_in", 0) > 60:
        return tokens["access_token"]
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": tokens["client_id"], "client_secret": tokens["client_secret"],
        "refresh_token": tokens["refresh_token"], "grant_type": "refresh_token"})
    if not r.ok:
        print(f"ERROR refreshing token: {r.text}"); sys.exit(1)
    tokens["access_token"] = r.json()["access_token"]
    json.dump(tokens, open(TOKEN_FILE, "w"), indent=2)
    return tokens["access_token"]


def drive_list(token, folder_id):
    items, page_token = [], None
    while True:
        params = {
            "q": f"'{folder_id}' in parents",
            "fields": "nextPageToken,files(id,name,mimeType,size)",
            "pageSize": 100,
        }
        if page_token:
            params["pageToken"] = page_token
        r = requests.get("https://www.googleapis.com/drive/v3/files",
                         headers={"Authorization": f"Bearer {token}"}, params=params)
        r.raise_for_status()
        data = r.json()
        items.extend(data.get("files", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return items


def drive_download(token, file_id, local_path):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"}, stream=True)
    r.raise_for_status()
    with open(local_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)


def drive_delete_existing(token, filename, folder_id):
    r = requests.get("https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": f"'{folder_id}' in parents and name='{filename}'",
                "fields": "files(id,name)"})
    r.raise_for_status()
    for f in r.json().get("files", []):
        requests.delete(f"https://www.googleapis.com/drive/v3/files/{f['id']}",
                        headers={"Authorization": f"Bearer {token}"}).raise_for_status()
        print(f"  Deleted existing {f['name']}")


def drive_upload(token, local_path, filename, folder_id, mime="video/mp4"):
    with open(local_path, "rb") as f:
        data = f.read()
    metadata = json.dumps({"name": filename, "parents": [folder_id]}).encode()
    boundary = b"upload_boundary_clips"
    body = (b"--" + boundary + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" +
            metadata + b"\r\n--" + boundary + b"\r\nContent-Type: " + mime.encode() +
            b"\r\n\r\n" + data + b"\r\n--" + boundary + b"--")
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files"
        "?uploadType=multipart&fields=id,name,webViewLink",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": f"multipart/related; boundary={boundary.decode()}"},
        data=body)
    if not r.ok:
        print(f"  Upload error {r.status_code}: {r.text}")
    r.raise_for_status()
    return r.json()


def run_ffmpeg(*args, label="ffmpeg"):
    cmd = ["ffmpeg", "-y"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n  ERROR [{label}]:\n{result.stderr[-800:]}")
        sys.exit(1)


def probe_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True)
    return float(result.stdout.strip())


def scene_num_from_name(name):
    m = re.match(r"^(\d+)_", name)
    return int(m.group(1)) if m else 999


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 create_video_from_clips.py <episode_folder_id> [output_filename]")
        sys.exit(1)

    folder_id = sys.argv[1]
    out_name  = sys.argv[2] if len(sys.argv) > 2 else "episode.mp4"

    os.makedirs(WORK_DIR, exist_ok=True)

    print("Authenticating...")
    token = get_access_token()
    print("  ✓ Authenticated")

    # ── Discover episode folder contents ─────────────────────────────────────
    print("Scanning episode folder...")
    items = drive_list(token, folder_id)

    videos_folder = next((f for f in items
                          if f["name"].lower() == "videos" and "folder" in f["mimeType"]), None)
    if not videos_folder:
        print("ERROR: No 'Videos' subfolder found"); sys.exit(1)

    timings_file = next((f for f in items if f["name"] == "audio_timings_new.csv"), None)
    if not timings_file:
        print("ERROR: audio_timings_new.csv not found"); sys.exit(1)

    AUDIO_MIMES = ("audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav")
    audio_file = next((f for f in items if f.get("mimeType", "") in AUDIO_MIMES), None)
    if not audio_file:
        audio_folder = next((f for f in items if f.get("name", "").lower() == "audio"
                             and "folder" in f.get("mimeType", "")), None)
        if audio_folder:
            sub = drive_list(token, audio_folder["id"])
            candidates = [f for f in sub if f.get("mimeType", "") in AUDIO_MIMES]
            if candidates:
                audio_file = max(candidates, key=lambda f: int(f.get("size", 0)))
    if not audio_file:
        print("ERROR: No audio file found"); sys.exit(1)

    # ── Load timings ──────────────────────────────────────────────────────────
    print("Downloading timings...")
    timings_path = os.path.join(WORK_DIR, "timings.csv")
    drive_download(token, timings_file["id"], timings_path)
    timings = {}
    with open(timings_path) as f:
        for row in csv.DictReader(f):
            timings[int(row["scene"])] = float(row["duration_seconds"])
    print(f"  ✓ {len(timings)} scenes")

    # ── Download audio ────────────────────────────────────────────────────────
    print(f"Downloading audio: {audio_file['name']}...")
    audio_ext  = ".wav" if "wav" in audio_file.get("mimeType", "") else ".mp3"
    audio_path = os.path.join(WORK_DIR, f"audio{audio_ext}")
    drive_download(token, audio_file["id"], audio_path)
    print(f"  ✓ {os.path.getsize(audio_path):,} bytes")

    # ── List & sort clips ─────────────────────────────────────────────────────
    print("Listing video clips...")
    all_clips = drive_list(token, videos_folder["id"])
    clips = [c for c in all_clips if c.get("mimeType") == "video/mp4"]
    clips.sort(key=lambda c: scene_num_from_name(c["name"]))
    print(f"  ✓ {len(clips)} clips found")

    # ── Process each clip ─────────────────────────────────────────────────────
    processed_paths = []
    for clip in clips:
        sn        = scene_num_from_name(clip["name"])
        scene_dur = timings.get(sn)
        if scene_dur is None:
            print(f"  WARNING: No timing for scene {sn}, skipping"); continue

        raw_path  = os.path.join(WORK_DIR, f"raw_{sn:03d}.mp4")
        proc_path = os.path.join(WORK_DIR, f"proc_{sn:03d}.mp4")

        # Download (resume-safe)
        if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
            print(f"  [{sn:2d}/{len(clips)}] Downloading {clip['name'][:50]}...", end=" ", flush=True)
            drive_download(token, clip["id"], raw_path)
            print("✓")
        else:
            print(f"  [{sn:2d}/{len(clips)}] Already downloaded, using cached")

        # Get actual clip duration via ffprobe
        clip_dur = probe_duration(raw_path)

        if abs(scene_dur - clip_dur) < 0.15:
            # Within 150ms — copy as-is
            shutil.copy(raw_path, proc_path)
            print(f"           {clip_dur:.2f}s clip = {scene_dur:.2f}s scene → copy")

        elif scene_dur > clip_dur:
            # Scene is longer than clip — slow down
            pts = scene_dur / clip_dur
            print(f"           {clip_dur:.2f}s clip → {scene_dur:.2f}s scene  (slow {pts:.3f}x)")
            run_ffmpeg(
                "-i", raw_path,
                "-vf", f"setpts={pts:.6f}*PTS",
                "-r", "24",
                "-t", f"{scene_dur:.3f}",
                "-an", "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                proc_path, label=f"scene {sn} slow")

        else:
            # Scene is shorter than clip — trim at 1.0x speed
            print(f"           {clip_dur:.2f}s clip → {scene_dur:.2f}s scene  (trim)")
            run_ffmpeg(
                "-i", raw_path,
                "-t", f"{scene_dur:.3f}",
                "-an", "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                proc_path, label=f"scene {sn} trim")

        processed_paths.append(proc_path)

    print(f"\n✓ {len(processed_paths)} clips processed")

    # ── Concatenate ───────────────────────────────────────────────────────────
    concat_list = os.path.join(WORK_DIR, "concat_list.txt")
    with open(concat_list, "w") as f:
        for p in processed_paths:
            f.write(f"file '{p}'\n")

    raw_video = os.path.join(WORK_DIR, "raw_video.mp4")
    print("Concatenating clips...")
    run_ffmpeg(
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        raw_video, label="concatenate")
    print(f"  ✓ {os.path.getsize(raw_video):,} bytes")

    # ── Add audio ─────────────────────────────────────────────────────────────
    final_path = os.path.join(WORK_DIR, "final.mp4")
    print("Adding audio...")
    run_ffmpeg(
        "-i", raw_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        final_path, label="add audio")
    size_mb = os.path.getsize(final_path) / 1_000_000
    print(f"  ✓ Final: {size_mb:.1f} MB")

    # ── Upload ────────────────────────────────────────────────────────────────
    print(f"\nUploading {out_name} to Drive...")
    token = get_access_token()
    drive_delete_existing(token, out_name, folder_id)
    result = drive_upload(token, final_path, out_name, folder_id)
    print(f"  ✓ Uploaded: {result['name']}")
    print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")

    # ── Cleanup ───────────────────────────────────────────────────────────────
    for p in processed_paths:
        if os.path.exists(p): os.remove(p)
    for tmp in [raw_video, concat_list]:
        if os.path.exists(tmp): os.remove(tmp)
    print("  ✓ Temp files cleaned up")


if __name__ == "__main__":
    main()
