#!/usr/bin/env python3
"""
Create a 30-second sample preview video with Ken Burns + karaoke subtitles.
Uses the first N scenes that fill ~SAMPLE_DURATION seconds.
Uploads as 'sample_30s.mp4' to the episode folder.

Usage:
    python3 create_sample.py <episode_folder_id> [--crossfade]
"""

import csv, io, json, os, re, subprocess, sys, tempfile, shutil, requests
from pathlib import Path

TOKEN_FILE     = "/home/user/ClaudeCode/token.json"
SAMPLE_DURATION = 30.0   # target sample length in seconds
OUTPUT_LOCAL   = "/home/user/ClaudeCode/sample_30s.mp4"
RESOLUTION_W   = 1920
RESOLUTION_H   = 1080
FPS            = 30
VIDEO_CRF      = 23

KB_SCALE = 1.2

# Karaoke config (matches create_video_kb.py)
SUB_FONT_SIZE  = 80
SUB_MARGIN_V   = 80
SUB_PHRASE_LEN = 4
SUB_BORD_NORM  = 2
SUB_BORD_HL    = 20

# Crossfade duration in seconds (used with --crossfade flag)
XFADE_DURATION = 0.3

# ── Auth ──────────────────────────────────────────────────────────────────────
def load_tokens():
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
    r.raise_for_status()
    tokens["access_token"] = r.json()["access_token"]
    save_tokens(tokens)
    return tokens["access_token"]

# ── Drive helpers ─────────────────────────────────────────────────────────────
def drive_list_files(token, folder_id, mime_filter=None):
    files, page_token = [], None
    while True:
        q = f"'{folder_id}' in parents"
        if mime_filter:
            q += f" and mimeType contains '{mime_filter}'"
        params = {"q": q, "fields": "nextPageToken,files(id,name,mimeType)", "pageSize": 200}
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

def drive_get_name(token, file_id):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"fields": "name"},
    )
    r.raise_for_status()
    return r.json()["name"]

def drive_download(token, file_id, local_path):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"}, stream=True,
    )
    r.raise_for_status()
    with open(local_path, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)

def drive_load_csv(token, file_id):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.content.decode("utf-8"))))

def drive_delete_existing(token, filename, folder_id):
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

def drive_upload(token, local_path, filename, folder_id):
    with open(local_path, "rb") as f:
        data = f.read()
    metadata = json.dumps({"name": filename, "parents": [folder_id]}).encode()
    boundary = b"vid_boundary_xyz"
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n" +
        metadata + b"\r\n"
        b"--" + boundary + b"\r\n"
        b"Content-Type: video/mp4\r\n\r\n" +
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
    r.raise_for_status()
    return r.json()

# ── Ken Burns ─────────────────────────────────────────────────────────────────
EFFECT_NAMES = ["pan left→right", "pan right→left", "pan top→bottom", "pan bottom→top"]

def get_kb_filter(idx, duration, w, h):
    D  = duration
    LW = int(w * KB_SCALE)
    LH = int(h * KB_SCALE)
    px = LW - w
    py = LH - h
    cx = px // 2
    cy = py // 2
    P  = f"min(t/{D:.6f},1)"
    effects = [
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=white,"
         f"crop=w={w}:h={h}:x='{px}*{P}':y={cy},scale={w}:{h},setsar=1"),
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=white,"
         f"crop=w={w}:h={h}:x='{px}*(1-{P})':y={cy},scale={w}:{h},setsar=1"),
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=white,"
         f"crop=w={w}:h={h}:x={cx}:y='{py}*{P}',scale={w}:{h},setsar=1"),
        (f"scale={LW}:{LH}:force_original_aspect_ratio=decrease,"
         f"pad={LW}:{LH}:(ow-iw)/2:(oh-ih)/2:color=white,"
         f"crop=w={w}:h={h}:x={cx}:y='{py}*(1-{P})',scale={w}:{h},setsar=1"),
    ]
    return effects[idx % 4]

static_vf = (
    f"scale={RESOLUTION_W}:{RESOLUTION_H}:force_original_aspect_ratio=decrease,"
    f"pad={RESOLUTION_W}:{RESOLUTION_H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
)

# ── Subtitle generation ───────────────────────────────────────────────────────
def seconds_to_ass(t):
    h = int(t) // 3600
    m = (int(t) % 3600) // 60
    s = t - h * 3600 - m * 60
    return f"{h}:{m:02d}:{s:05.2f}"

def generate_ass_karaoke(timing_rows):
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Sub,Arial,{SUB_FONT_SIZE},"
        f"&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,"
        f"1,0,0,0,100,100,0,0,1,{SUB_BORD_NORM},0,"
        f"2,40,40,{SUB_MARGIN_V},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events = []
    for row in timing_rows:
        text = row.get("narration_excerpt", "").strip()
        if not text:
            continue
        try:
            start_s = float(row["start_seconds"])
            end_s   = float(row["end_seconds"])
        except (KeyError, ValueError):
            continue
        dur = end_s - start_s
        if dur <= 0:
            continue
        words = text.upper().split()
        n = len(words)
        if not n:
            continue
        word_dur = dur / n
        for phrase_start in range(0, n, SUB_PHRASE_LEN):
            phrase_words = words[phrase_start:min(phrase_start + SUB_PHRASE_LEN, n)]
            for local_i, _ in enumerate(phrase_words):
                global_i = phrase_start + local_i
                t_start  = start_s + global_i * word_dur
                t_end    = start_s + (global_i + 1) * word_dur
                if global_i == n - 1:
                    t_end = end_s
                parts = []
                for j, w in enumerate(phrase_words):
                    if j == local_i:
                        parts.append(
                            f"{{\\bord{SUB_BORD_HL}\\3c&H0000FF00&}}{w}"
                            f"{{\\bord{SUB_BORD_NORM}\\3c&H00000000&}}"
                        )
                    else:
                        parts.append(w)
                text_field = "{\\an2}" + " ".join(parts)
                events.append(
                    f"Dialogue: 0,{seconds_to_ass(t_start)},{seconds_to_ass(t_end)},"
                    f"Sub,,0,0,0,,{text_field}"
                )
    return header + "\n".join(events) + "\n"

# ── Rendering ─────────────────────────────────────────────────────────────────
def render_segment(image_path, seg_path, duration, vf):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(FPS), "-i", image_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", str(VIDEO_CRF),
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-t", f"{duration:.6f}",
        seg_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-800:]}")
        sys.exit(1)

def concat_simple(segments, merged_path):
    """Concatenate segments with stream copy (no transition)."""
    concat_file = merged_path + ".concat.txt"
    with open(concat_file, "w") as f:
        for s in segments:
            f.write(f"file '{s}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
         "-c:v", "copy", merged_path],
        capture_output=True, check=True,
    )
    os.unlink(concat_file)

def concat_crossfade(segments, durations, merged_path):
    """
    Concatenate segments with crossfade dissolve transitions using xfade filter.
    Each transition overlaps by XFADE_DURATION seconds.
    """
    if len(segments) == 1:
        import shutil as _sh
        _sh.copy(segments[0], merged_path)
        return

    xd = XFADE_DURATION
    # Build complex ffmpeg filter for xfade chaining
    inputs = []
    for s in segments:
        inputs += ["-i", s]

    # Compute offset for each transition = cumulative duration - xd per transition
    filter_parts = []
    cumulative = 0.0
    prev_out = "[0:v]"
    for i in range(1, len(segments)):
        cumulative += durations[i - 1] - xd
        out = f"[v{i}]" if i < len(segments) - 1 else "[vout]"
        filter_parts.append(
            f"{prev_out}[{i}:v]xfade=transition=dissolve:"
            f"duration={xd}:offset={cumulative:.4f}{out}"
        )
        prev_out = out

    filter_str = ";".join(filter_parts)
    cmd = (
        ["ffmpeg", "-y"] + inputs +
        ["-filter_complex", filter_str, "-map", "[vout]",
         "-c:v", "libx264", "-preset", "fast", "-crf", str(VIDEO_CRF),
         "-pix_fmt", "yuv420p", "-r", str(FPS), merged_path]
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  xfade error — falling back to simple concat:\n{result.stderr[-600:]}")
        concat_simple(segments, merged_path)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args  = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if not args:
        print("Usage: python3 create_sample.py <episode_folder_id> [--crossfade]")
        sys.exit(1)

    folder_id   = args[0]
    use_xfade   = "--crossfade" in flags

    print("Authenticating...")
    token = get_access_token()
    folder_name = drive_get_name(token, folder_id)
    print(f"  ✓ Episode: {folder_name}")
    print(f"  Crossfade: {'ON (0.3s dissolve)' if use_xfade else 'OFF (hard cuts)'}")

    # Find images subfolder
    all_files = drive_list_files(token, folder_id)
    img_folder = next((f for f in all_files if f["name"].lower() == "images"
                       and "folder" in f["mimeType"]), None)
    if not img_folder:
        print("ERROR: No Images subfolder found.")
        sys.exit(1)

    image_files = drive_list_files(token, img_folder["id"], mime_filter="image/")
    image_files = [f for f in image_files if f["mimeType"].startswith("image/")]
    def leading_num(f):
        m = re.match(r'^(\d+)_', f["name"])
        return int(m.group(1)) if m else 9999
    image_files.sort(key=leading_num)
    print(f"  ✓ {len(image_files)} total images in folder")

    # Find timings CSV and audio
    timings_file = (
        next((f for f in all_files if f["name"] == "audio_timings_new.csv"), None) or
        next((f for f in all_files if f["name"] == "auto_timings.csv"), None)
    )
    audio_file = next((f for f in all_files if f["name"] == "narration.mp3"), None)
    if not timings_file:
        print("ERROR: No timings CSV found (audio_timings_new.csv).")
        sys.exit(1)
    if not audio_file:
        print("ERROR: narration.mp3 not found.")
        sys.exit(1)

    # Load timings and pick scenes up to SAMPLE_DURATION
    print("Loading timings CSV...")
    timing_rows = drive_load_csv(token, timings_file["id"])
    timing_rows.sort(key=lambda r: int(r["scene"]))

    has_seconds = "start_seconds" in timing_rows[0]
    if not has_seconds:
        print("ERROR: timings CSV missing start_seconds — re-run generate_timings.py first.")
        sys.exit(1)

    # Select scenes that fit within the sample duration
    sample_rows = []
    cumulative  = 0.0
    for row in timing_rows:
        dur = float(row["duration_seconds"])
        if cumulative + dur > SAMPLE_DURATION + 1.0:
            break
        sample_rows.append(row)
        cumulative += dur

    n_scenes = len(sample_rows)
    actual_duration = sum(float(r["duration_seconds"]) for r in sample_rows)
    print(f"  ✓ Selected {n_scenes} scenes covering {actual_duration:.1f}s")

    # Match scenes to image files (1-indexed)
    scene_nums   = [int(r["scene"]) for r in sample_rows]
    sample_imgs  = [f for f in image_files if leading_num(f) in scene_nums]
    sample_imgs.sort(key=leading_num)

    if len(sample_imgs) != n_scenes:
        print(f"  ⚠ Image count mismatch: {len(sample_imgs)} images for {n_scenes} scenes — using available")
        n_scenes = min(len(sample_imgs), n_scenes)
        sample_rows = sample_rows[:n_scenes]
        sample_imgs = sample_imgs[:n_scenes]

    tmpdir = tempfile.mkdtemp(prefix="mf_sample_")
    try:
        print(f"\nDownloading {n_scenes} images + audio...")
        local_imgs = []
        for i, img in enumerate(sample_imgs):
            ext = os.path.splitext(img["name"])[1] or ".jpg"
            lp  = os.path.join(tmpdir, f"scene_{i+1:03d}{ext}")
            drive_download(token, img["id"], lp)
            local_imgs.append(lp)

        audio_full = os.path.join(tmpdir, "narration.mp3")
        drive_download(token, audio_file["id"], audio_full)

        # Trim audio to sample length
        audio_trim = os.path.join(tmpdir, "audio_trim.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_full,
             "-t", f"{actual_duration:.3f}", "-c:a", "copy", audio_trim],
            capture_output=True, check=True,
        )
        print("  ✓ Audio trimmed")

        # Render segments
        print(f"\nRendering {n_scenes} segments...")
        segments  = []
        durations = []
        kb_cycle  = 0
        w, h      = RESOLUTION_W, RESOLUTION_H

        for i, (img, row) in enumerate(zip(local_imgs, sample_rows)):
            dur = float(row["duration_seconds"])
            durations.append(dur)
            seg = os.path.join(tmpdir, f"seg_{i:03d}.mp4")

            if i > 0 and i % 4 == 1:
                vf    = get_kb_filter(kb_cycle % 4, dur, w, h)
                label = EFFECT_NAMES[kb_cycle % 4]
                kb_cycle += 1
                print(f"  Scene {i+1}: {dur:.1f}s  KB {label}")
            else:
                vf = static_vf

            render_segment(img, seg, dur, vf)
            segments.append(seg)

        # Concatenate
        merged = os.path.join(tmpdir, "merged.mp4")
        print(f"\nConcatenating ({'xfade dissolve' if use_xfade else 'hard cuts'})...")
        if use_xfade:
            concat_crossfade(segments, durations, merged)
        else:
            concat_simple(segments, merged)

        # Mux audio
        muxed = os.path.join(tmpdir, "muxed.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-i", merged, "-i", audio_trim,
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", "-shortest", muxed],
            capture_output=True, check=True,
        )

        # Burn subtitles
        print("Generating karaoke subtitles...")
        ass_content = generate_ass_karaoke(sample_rows)
        ass_path    = os.path.join(tmpdir, "subtitles.ass")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        safe_ass = ass_path.replace("\\", "/").replace(":", "\\:")
        result = subprocess.run([
            "ffmpeg", "-y", "-i", muxed,
            "-vf", f"ass={safe_ass}",
            "-c:v", "libx264", "-preset", "fast", "-crf", str(VIDEO_CRF),
            "-c:a", "copy", OUTPUT_LOCAL,
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  Subtitle error:\n{result.stderr[-1500:]}")
            sys.exit(1)

        size_mb = os.path.getsize(OUTPUT_LOCAL) / 1024 / 1024
        print(f"  ✓ Sample created ({size_mb:.1f} MB)")

        # Upload
        print("\nUploading sample_30s.mp4 to Drive...")
        token = get_access_token()
        drive_delete_existing(token, "sample_30s.mp4", folder_id)
        result = drive_upload(token, OUTPUT_LOCAL, "sample_30s.mp4", folder_id)
        print(f"  ✓ Uploaded: {result['name']}")
        print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")
        print(f"\nDone — {n_scenes} scenes, {actual_duration:.1f}s, KB + karaoke subtitles")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
