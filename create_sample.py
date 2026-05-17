#!/usr/bin/env python3
"""
Create a 30-second sample preview video with Ken Burns + karaoke subtitles.
Subtitles use PIL to render a proper solid green rectangle behind the active word.

Usage:
    python3 create_sample.py <episode_folder_id> [--crossfade] [--output=sample_30s.mp4]
"""

import csv, io, json, os, re, subprocess, sys, tempfile, shutil, requests
from PIL import Image, ImageDraw, ImageFont

TOKEN_FILE      = "/home/user/ClaudeCode/token.json"
SAMPLE_DURATION = 30.0
OUTPUT_LOCAL    = "/home/user/ClaudeCode/sample_30s.mp4"
RESOLUTION_W    = 1920
RESOLUTION_H    = 1080
FPS             = 30
VIDEO_CRF       = 23
KB_SCALE        = 1.2
XFADE_DURATION  = 0.3

# Subtitle config
FONT_PATH       = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_SIZE       = 80
PHRASE_LEN      = 4          # words per phrase group
BOX_PAD_H       = 18         # horizontal padding inside green box
BOX_PAD_V       = 10         # vertical padding inside green box
BOX_RADIUS      = 8          # rounded corner radius (0 = sharp rectangle)
SUB_MARGIN_V    = 90         # pixels from bottom of frame to text baseline

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

# ── PIL subtitle rendering ────────────────────────────────────────────────────
def build_subtitle_events(timing_rows):
    """
    Returns list of (t_start, t_end, phrase_words, active_idx) tuples.
    """
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
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
        words    = text.upper().split()
        n        = len(words)
        word_dur = dur / n
        for phrase_start in range(0, n, PHRASE_LEN):
            phrase_words = words[phrase_start:min(phrase_start + PHRASE_LEN, n)]
            for local_i in range(len(phrase_words)):
                global_i = phrase_start + local_i
                t_start  = start_s + global_i * word_dur
                t_end    = start_s + (global_i + 1) * word_dur
                if global_i == n - 1:
                    t_end = end_s
                events.append((t_start, t_end, phrase_words, local_i))
    return events, font

def render_subtitle_frame(phrase_words, active_idx, font, w=RESOLUTION_W, h=RESOLUTION_H):
    """
    Render a 1920×1080 RGBA frame: all phrase words in white bold, with a
    solid green rounded rectangle behind the currently active word.
    """
    img  = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Measure each word
    word_metrics = []
    for word in phrase_words:
        bb = font.getbbox(word)
        word_metrics.append((bb[2] - bb[0], bb[3] - bb[1]))   # (width, height)

    space_bb  = font.getbbox(" ")
    space_w   = space_bb[2] - space_bb[0]
    total_w   = sum(wm[0] for wm in word_metrics) + space_w * (len(phrase_words) - 1)
    max_h     = max(wm[1] for wm in word_metrics)

    x_start   = (w - total_w) // 2
    y_text    = h - SUB_MARGIN_V - max_h

    # Calculate per-word x positions
    word_xs = []
    x = x_start
    for i, (ww, wh) in enumerate(word_metrics):
        word_xs.append(x)
        x += ww + space_w

    # Draw solid green rectangle behind active word
    ax  = word_xs[active_idx]
    aw  = word_metrics[active_idx][0]
    ah  = max_h
    x1  = ax - BOX_PAD_H
    y1  = y_text - BOX_PAD_V
    x2  = ax + aw + BOX_PAD_H
    y2  = y_text + ah + BOX_PAD_V
    if BOX_RADIUS > 0:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=BOX_RADIUS, fill=(0, 200, 0, 255))
    else:
        draw.rectangle([x1, y1, x2, y2], fill=(0, 200, 0, 255))

    # Draw each word: black stroke outline + white fill
    for i, (word, wx) in enumerate(zip(phrase_words, word_xs)):
        draw.text(
            (wx, y_text), word, font=font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255),
        )

    return img

def build_subtitle_overlay(events, font, tmpdir, total_duration):
    """
    Generates per-event subtitle PNGs, writes a concat file, and renders
    a transparent MOV overlay (PNG codec, RGBA).
    Returns path to overlay .mov file.
    """
    blank_path = os.path.join(tmpdir, "sub_blank.png")
    Image.new("RGBA", (RESOLUTION_W, RESOLUTION_H), (0, 0, 0, 0)).save(blank_path)

    # Cache rendered frames by (phrase, active_idx)
    frame_cache = {}
    def get_frame(phrase_words, active_idx):
        key = (tuple(phrase_words), active_idx)
        if key not in frame_cache:
            img  = render_subtitle_frame(phrase_words, active_idx, font)
            path = os.path.join(tmpdir, f"subf_{len(frame_cache):05d}.png")
            img.save(path)
            frame_cache[key] = path
        return frame_cache[key]

    # Build concat entries: blank from 0 → first event, then each event
    concat_entries = []   # list of (path, duration)

    cursor = 0.0
    for t_start, t_end, phrase_words, active_idx in events:
        if t_start > cursor + 0.001:
            concat_entries.append((blank_path, t_start - cursor))
        concat_entries.append((get_frame(phrase_words, active_idx), t_end - t_start))
        cursor = t_end

    if cursor < total_duration - 0.001:
        concat_entries.append((blank_path, total_duration - cursor))

    # Write concat file
    concat_path = os.path.join(tmpdir, "sub_concat.txt")
    with open(concat_path, "w") as f:
        for path, dur in concat_entries:
            f.write(f"file '{path}'\n")
            f.write(f"duration {dur:.6f}\n")
        # Repeat last entry (ffmpeg concat demuxer quirk)
        if concat_entries:
            f.write(f"file '{concat_entries[-1][0]}'\n")

    # Render subtitle overlay video (RGBA transparent MOV)
    overlay_path = os.path.join(tmpdir, "subtitle_overlay.mov")
    result = subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_path,
        "-vf", f"fps={FPS}",
        "-c:v", "png", "-pix_fmt", "rgba",
        overlay_path,
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Subtitle overlay error:\n{result.stderr[-1500:]}")
        sys.exit(1)

    print(f"  ✓ Subtitle overlay: {len(frame_cache)} unique frames, {len(concat_entries)} events")
    return overlay_path

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
        print(f"  ffmpeg error:\n{result.stderr[-800:]}")
        sys.exit(1)

def concat_simple(segments, merged_path):
    concat_file = merged_path + ".txt"
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
    if len(segments) == 1:
        shutil.copy(segments[0], merged_path)
        return
    xd      = XFADE_DURATION
    inputs  = []
    for s in segments:
        inputs += ["-i", s]
    parts   = []
    cumul   = 0.0
    prev    = "[0:v]"
    for i in range(1, len(segments)):
        cumul += durations[i - 1] - xd
        out    = f"[v{i}]" if i < len(segments) - 1 else "[vout]"
        parts.append(
            f"{prev}[{i}:v]xfade=transition=dissolve:"
            f"duration={xd}:offset={cumul:.4f}{out}"
        )
        prev = out
    cmd = (
        ["ffmpeg", "-y"] + inputs +
        ["-filter_complex", ";".join(parts), "-map", "[vout]",
         "-c:v", "libx264", "-preset", "fast", "-crf", str(VIDEO_CRF),
         "-pix_fmt", "yuv420p", "-r", str(FPS), merged_path]
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  xfade error — falling back to hard cuts:\n{result.stderr[-600:]}")
        concat_simple(segments, merged_path)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args  = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a.lstrip("-").split("=")[0]: (a.split("=")[1] if "=" in a else True)
             for a in sys.argv[1:] if a.startswith("--")}

    if not args:
        print("Usage: python3 create_sample.py <episode_folder_id> [--crossfade] [--output=filename.mp4]")
        sys.exit(1)

    folder_id  = args[0]
    use_xfade  = "crossfade" in flags
    out_name   = flags.get("output", "sample_30s.mp4")
    local_out  = f"/home/user/ClaudeCode/{out_name}"

    print("Authenticating...")
    token = get_access_token()
    folder_name = drive_get_name(token, folder_id)
    print(f"  ✓ Episode: {folder_name}")
    print(f"  Transitions: {'crossfade 0.3s dissolve' if use_xfade else 'hard cuts'}")

    all_files  = drive_list_files(token, folder_id)
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
    print(f"  ✓ {len(image_files)} total images")

    timings_file = (
        next((f for f in all_files if f["name"] == "audio_timings_new.csv"), None) or
        next((f for f in all_files if f["name"] == "auto_timings.csv"), None)
    )
    audio_file = next((f for f in all_files if f["name"] == "narration.mp3"), None)
    if not timings_file or not audio_file:
        print("ERROR: Missing audio_timings_new.csv or narration.mp3")
        sys.exit(1)

    print("Loading timings...")
    timing_rows = drive_load_csv(token, timings_file["id"])
    timing_rows.sort(key=lambda r: int(r["scene"]))
    if "start_seconds" not in timing_rows[0]:
        print("ERROR: CSV missing start_seconds — re-run generate_timings.py")
        sys.exit(1)

    # Pick scenes covering ~SAMPLE_DURATION seconds
    sample_rows = []
    cumulative  = 0.0
    for row in timing_rows:
        dur = float(row["duration_seconds"])
        if cumulative + dur > SAMPLE_DURATION + 1.0:
            break
        sample_rows.append(row)
        cumulative += dur

    n_scenes        = len(sample_rows)
    actual_duration = sum(float(r["duration_seconds"]) for r in sample_rows)
    print(f"  ✓ {n_scenes} scenes, {actual_duration:.1f}s")

    scene_nums  = {int(r["scene"]) for r in sample_rows}
    sample_imgs = [f for f in image_files if leading_num(f) in scene_nums]
    sample_imgs.sort(key=leading_num)
    n_scenes    = min(len(sample_imgs), n_scenes)
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
        audio_trim = os.path.join(tmpdir, "audio_trim.mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-i", audio_full,
             "-t", f"{actual_duration:.3f}", "-c:a", "copy", audio_trim],
            capture_output=True, check=True,
        )
        print("  ✓ Audio trimmed")

        # Render KB segments
        print(f"\nRendering {n_scenes} segments (KB_SCALE=1.2)...")
        segments  = []
        durations = []
        kb_cycle  = 0
        for i, (img_path, row) in enumerate(zip(local_imgs, sample_rows)):
            dur = float(row["duration_seconds"])
            durations.append(dur)
            seg = os.path.join(tmpdir, f"seg_{i:03d}.mp4")
            if i > 0 and i % 4 == 1:
                vf    = get_kb_filter(kb_cycle % 4, dur, RESOLUTION_W, RESOLUTION_H)
                label = EFFECT_NAMES[kb_cycle % 4]
                kb_cycle += 1
                print(f"  Scene {i+1}: {dur:.1f}s  KB {label}")
            else:
                vf = static_vf
            render_segment(img_path, seg, dur, vf)
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

        # Build PIL subtitle overlay
        print("\nGenerating subtitle overlay (PIL solid green box)...")
        events, font = build_subtitle_events(sample_rows)
        overlay_path = build_subtitle_overlay(events, font, tmpdir, actual_duration)

        # Composite: main video + subtitle overlay
        print("  Compositing subtitles onto video...")
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", muxed,
            "-i", overlay_path,
            "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1",
            "-c:v", "libx264", "-preset", "fast", "-crf", str(VIDEO_CRF),
            "-c:a", "copy",
            local_out,
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  Composite error:\n{result.stderr[-1500:]}")
            sys.exit(1)

        size_mb = os.path.getsize(local_out) / 1024 / 1024
        print(f"  ✓ Done ({size_mb:.1f} MB)")

        # Upload
        print(f"\nUploading {out_name} to Drive...")
        token = get_access_token()
        drive_delete_existing(token, out_name, folder_id)
        result = drive_upload(token, local_out, out_name, folder_id)
        print(f"  ✓ {result['name']}")
        print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")
        print(f"\nDone — {n_scenes} scenes, {actual_duration:.1f}s")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
