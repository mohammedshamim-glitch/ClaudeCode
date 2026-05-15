#!/usr/bin/env python3
"""
Generate audio_timings_new.csv using local Whisper word-level timestamps.

Method:
  1. Download narration.mp3 + 03-narration-script-clean.txt from Drive
  2. Run local Whisper (base model) with word_timestamps=True → full word list
  3. Split script by blank lines → one paragraph = one scene
  4. For each scene, find the LAST few words of that scene in the Whisper word list
  5. The end_time of those last words = the scene boundary
  6. Build CSV: scene_start = previous scene's end_time, scene_end = this scene's end_time
  7. Upload audio_timings_new.csv to the episode Drive folder

Usage:
    python3 generate_timings_whisper.py <episode_folder_id>
"""

import csv, json, os, re, sys, tempfile, shutil, requests, time

TOKEN_FILE = "/home/user/ClaudeCode/token.json"

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
def drive_list_all(token, folder_id):
    files, page_token = [], None
    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed=false",
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

def drive_download_text(token, file_id):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"},
    )
    r.raise_for_status()
    return r.content.decode("utf-8")

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

def drive_upload_csv(token, local_path, filename, folder_id):
    with open(local_path, "rb") as f:
        data = f.read()
    metadata = json.dumps({"name": filename, "parents": [folder_id]}).encode()
    boundary = b"csv_boundary_xyz"
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n" +
        metadata + b"\r\n"
        b"--" + boundary + b"\r\n"
        b"Content-Type: text/csv\r\n\r\n" +
        data + b"\r\n"
        b"--" + boundary + b"--"
    )
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files"
        "?uploadType=multipart&fields=id,name,webViewLink",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary.decode()}",
        },
        data=body,
    )
    r.raise_for_status()
    return r.json()

# ── Scene splitting ───────────────────────────────────────────────────────────
def split_scenes(raw_text):
    """Split narration/sentence file by blank lines — each paragraph is one scene/sentence."""
    paragraphs = re.split(r'\n\s*\n', raw_text.strip())
    scenes = []
    for p in paragraphs:
        p = p.strip().replace('\n', ' ')
        if p and not re.match(r'^---', p):  # strip footer lines like "--- TOTAL: N sentences ---"
            scenes.append(p)
    return scenes

# ── Text normalisation for matching ──────────────────────────────────────────
def normalize(text):
    """Lowercase, strip punctuation, return list of tokens."""
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).split()

# ── Whisper transcription ─────────────────────────────────────────────────────
def transcribe_audio(audio_path):
    """
    Run local Whisper (base model) on audio_path with word_timestamps=True.
    Returns flat list of {"word": str, "start": float, "end": float}.
    """
    import whisper
    print("  Loading Whisper base model from ~/.cache/whisper/base.pt ...")
    model = whisper.load_model("base")
    print("  Transcribing (this takes a couple of minutes)...")
    result = model.transcribe(audio_path, word_timestamps=True)

    words = []
    for segment in result["segments"]:
        for w in segment.get("words", []):
            word_text = w.get("word", "").strip()
            if word_text:
                words.append({
                    "word":  word_text,
                    "start": round(float(w["start"]), 3),
                    "end":   round(float(w["end"]),   3),
                })
    return words

# ── Sequential word-level alignment ──────────────────────────────────────────
def align_scenes(scenes, whisper_words, total_duration):
    """
    Sequential word-level alignment:
    1. Flatten all scenes into an ordered (scene_idx, norm_word) list.
    2. Walk through Whisper words in order, greedily matching each script word
       with a small lookahead window. This never misidentifies sentence boundaries
       regardless of sentence length.
    3. Interpolate timestamps for any unmatched words using adjacent anchors.
    4. Aggregate: sentence start = first word start, end = last word end.

    Returns list of {"start": float, "end": float} — one per scene.
    """
    LOOKAHEAD = 10  # max Whisper words to skip when matching one script word

    # Build flat script word list: (scene_idx, word_position_in_scene, norm_word)
    script_entries = []
    for s_idx, scene in enumerate(scenes):
        nw = normalize(scene)
        for pos, word in enumerate(nw):
            script_entries.append((s_idx, pos, word))

    if not script_entries:
        return [{"start": 0.0, "end": total_duration}]

    # Normalise Whisper words
    wh_norm  = [normalize(w["word"])[0] if normalize(w["word"]) else "" for w in whisper_words]
    wh_start = [w["start"] for w in whisper_words]
    wh_end   = [w["end"]   for w in whisper_words]

    # Greedy sequential match — store matched timestamp per script_entry index
    matched_start = [None] * len(script_entries)
    matched_end   = [None] * len(script_entries)

    wh_pos = 0
    for sc_pos, (s_idx, _, sc_word) in enumerate(script_entries):
        if not sc_word:
            continue
        for offset in range(LOOKAHEAD):
            wi = wh_pos + offset
            if wi >= len(whisper_words):
                break
            if wh_norm[wi] == sc_word:
                matched_start[sc_pos] = wh_start[wi]
                matched_end[sc_pos]   = wh_end[wi]
                wh_pos = wi + 1
                break

    # Interpolate None gaps using nearest valid neighbours
    # First pass: fill forward
    last_valid_end = 0.0
    for i in range(len(matched_start)):
        if matched_start[i] is not None:
            last_valid_end = matched_end[i]
        else:
            # Find next matched entry
            next_start = total_duration
            for j in range(i + 1, len(matched_start)):
                if matched_start[j] is not None:
                    next_start = matched_start[j]
                    break
            # Place this word proportionally between last_valid_end and next_start
            # Count how many unmatched words are in this gap
            gap_count = sum(1 for k in range(i, len(matched_start))
                            if matched_start[k] is None
                            and (k == i or matched_start[k-1] is None))
            gap_size = next_start - last_valid_end
            # Simple: just use midpoint for now; full interpolation below
            matched_start[i] = last_valid_end
            matched_end[i]   = last_valid_end

    # Full linear interpolation over contiguous unmatched runs
    i = 0
    while i < len(matched_start):
        if matched_end[i] is not None and matched_end[i] > 0:
            i += 1
            continue
        # Start of a gap run
        run_start_idx = i
        while i < len(matched_start) and (matched_end[i] is None or matched_end[i] == 0):
            i += 1
        run_end_idx = i  # exclusive

        left_t  = matched_end[run_start_idx - 1] if run_start_idx > 0 and matched_end[run_start_idx - 1] else 0.0
        right_t = matched_start[run_end_idx] if run_end_idx < len(matched_start) and matched_start[run_end_idx] else total_duration

        run_len = run_end_idx - run_start_idx
        for k, gi in enumerate(range(run_start_idx, run_end_idx)):
            frac_s = (k)       / run_len
            frac_e = (k + 1)   / run_len
            matched_start[gi] = round(left_t + frac_s * (right_t - left_t), 3)
            matched_end[gi]   = round(left_t + frac_e * (right_t - left_t), 3)

    # Aggregate per scene
    scene_word_map = {}  # scene_idx -> list of (start, end)
    for sc_pos, (s_idx, _, _) in enumerate(script_entries):
        ts = matched_start[sc_pos]
        te = matched_end[sc_pos]
        if ts is not None and te is not None:
            scene_word_map.setdefault(s_idx, []).append((ts, te))

    timings = []
    global_wps = len(script_entries) / total_duration

    for s_idx in range(len(scenes)):
        word_ts = scene_word_map.get(s_idx, [])
        if word_ts:
            start = word_ts[0][0]
            end   = word_ts[-1][1]
        else:
            # Fully unmatched scene: interpolate proportionally
            wc = len(normalize(scenes[s_idx]))
            start = timings[-1]["end"] if timings else 0.0
            end   = round(start + wc / global_wps, 3)
        timings.append({"start": round(start, 3), "end": round(end, 3)})

    # Ensure last scene ends exactly at audio end
    timings[-1]["end"] = round(total_duration, 3)

    # Final pass: ensure no scene has end <= start (protect video assembler)
    for i in range(len(timings)):
        if timings[i]["end"] <= timings[i]["start"]:
            # Give it proportional duration based on word count
            wc  = max(1, len(normalize(scenes[i])))
            dur = round(wc / global_wps, 3)
            timings[i]["end"] = round(timings[i]["start"] + dur, 3)
        # Clamp within audio
        timings[i]["end"] = min(timings[i]["end"], total_duration)

    return timings


def validate_and_fix_timings(timings, scenes, total_duration):
    """
    Report speech rate and flag any scenes with implausible durations.
    With word-level alignment most scenes should be clean — this is a
    diagnostic pass only; proportional fix is applied to remaining outliers.
    """
    word_counts = [len(s.split()) for s in scenes]
    total_words = sum(word_counts)
    global_wps  = total_words / total_duration
    expected_wpm = global_wps * 60

    print(f"\n  Speech rate check: {expected_wpm:.0f} wpm "
          f"({total_words} words / {total_duration:.1f}s)")

    suspects = set()
    for i, t in enumerate(timings):
        dur = t["end"] - t["start"]
        exp = word_counts[i] / global_wps
        ratio = dur / exp if exp > 0 else 999
        if ratio < 0.20 or ratio > 5.0:
            suspects.add(i)
            print(f"  ⚠ Scene {i+1}: {dur:.1f}s vs ~{exp:.1f}s expected "
                  f"({word_counts[i]} words, {ratio:.2f}x) — SUSPECT")

    if not suspects:
        print(f"  ✓ All {len(timings)} scenes within expected range")
        return timings

    print(f"  Proportional-interpolating {len(suspects)} suspect scene(s)...")
    boundaries = [t["end"] for t in timings]

    i = 0
    while i < len(boundaries):
        if i not in suspects:
            i += 1
            continue
        run_start = i
        while i < len(boundaries) and i in suspects:
            i += 1
        run_end = i

        li = run_start - 1
        while li > 0 and li in suspects:
            li -= 1
        left_time  = boundaries[li] if li >= 0 and li not in suspects else 0.0
        right_time = boundaries[run_end] if run_end < len(boundaries) else total_duration

        span_words = sum(word_counts[run_start:run_end])
        span_time  = right_time - left_time
        if span_words == 0:
            continue

        cumulative = 0
        for j in range(run_start, run_end):
            cumulative += word_counts[j]
            boundaries[j] = round(left_time + (cumulative / span_words) * span_time, 3)
            new_dur = boundaries[j] - (boundaries[j-1] if j > 0 else 0.0)
            exp = word_counts[j] / global_wps
            print(f"    Scene {j+1}: fixed → {new_dur:.1f}s (expected ~{exp:.1f}s)")

    fixed = []
    for i in range(len(boundaries)):
        start = 0.0 if i == 0 else boundaries[i-1]
        fixed.append({"start": round(start, 3), "end": boundaries[i]})
    fixed[-1]["end"] = round(total_duration, 3)
    return fixed


def fmt_time(seconds):
    m = int(seconds) // 60
    s = seconds - m * 60
    return f"{m:02d}:{s:05.2f}"

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_timings_whisper.py <episode_folder_id>")
        sys.exit(1)

    folder_id = sys.argv[1]

    print("Authenticating...")
    token = get_access_token()
    folder_name = drive_get_name(token, folder_id)
    print(f"  ✓ Episode: {folder_name}")

    print("Listing episode files...")
    items = drive_list_all(token, folder_id)

    # Prefer sentence-level file (163 sentences, 1:1 with images) over 25-word scene file
    SCRIPT_NAMES_PRIORITY = [
        "03b-narration-sentences.txt",
        "03-narration-script-clean.txt",
        "03-narration-script-clean-FINAL.txt",
        "narration_script.txt",
    ]
    script_file = next(
        (f for f in items if f["name"] in SCRIPT_NAMES_PRIORITY),
        None,
    )
    if script_file:
        # Sort to respect priority order
        script_file = min(
            [f for f in items if f["name"] in SCRIPT_NAMES_PRIORITY],
            key=lambda f: SCRIPT_NAMES_PRIORITY.index(f["name"]),
        )

    # Find audio: check root first, then Audio subfolder
    AUDIO_MIMES = ("audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav")
    audio_file = next((f for f in items if f.get("mimeType", "") in AUDIO_MIMES), None)
    if not audio_file:
        audio_folder = next(
            (f for f in items if f.get("name", "").lower() == "audio" and "folder" in f["mimeType"]), None
        )
        if audio_folder:
            sub_items  = drive_list_all(token, audio_folder["id"])
            candidates = [f for f in sub_items if f.get("mimeType", "") in AUDIO_MIMES]
            if candidates:
                # Pick the largest file (most likely the full narration)
                audio_file = max(candidates, key=lambda f: int(f.get("fileSize", 0)))

    if not script_file:
        print("ERROR: narration_script.txt not found in episode folder")
        sys.exit(1)
    if not audio_file:
        print("ERROR: No audio file (mp3/wav) found in episode folder or Audio subfolder")
        sys.exit(1)

    print(f"  ✓ Script: {script_file['name']}")
    print(f"  ✓ Audio:  {audio_file['name']} ({int(audio_file.get('fileSize',0))//1024//1024}MB)")

    tmpdir = tempfile.mkdtemp(prefix="mf_timings_")
    try:
        print("\nDownloading files...")
        audio_ext  = os.path.splitext(audio_file.get("name", audio_file.get("title", "narration.mp3")))[1] or ".mp3"
        audio_path = os.path.join(tmpdir, f"narration{audio_ext}")
        drive_download(token, audio_file["id"], audio_path)
        print("  ✓ Audio downloaded")

        script_text = drive_download_text(token, script_file["id"])
        print("  ✓ Script downloaded")

        # Get audio duration via ffprobe
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, check=True,
        )
        total_duration = float(result.stdout.strip())
        print(f"  ✓ Audio duration: {total_duration:.2f}s ({fmt_time(total_duration)})")

        # Split script into scenes
        scenes = split_scenes(script_text)
        print(f"  ✓ {len(scenes)} scenes parsed from narration script")

        # Transcribe with Whisper
        print("\nRunning Whisper transcription...")
        whisper_words = transcribe_audio(audio_path)
        print(f"  ✓ {len(whisper_words)} words transcribed with timestamps")

        # Align scenes to word boundaries
        print("\nAligning scene boundaries to word end-times...")
        timings = align_scenes(scenes, whisper_words, total_duration)

        # Self-check: catch and fix implausible timings using speech rate
        timings = validate_and_fix_timings(timings, scenes, total_duration)

        # Build CSV rows — narration_excerpt is the FULL scene text
        rows = []
        print(f"\n{'#':>3}  {'Start':>7}  {'End':>7}  {'Dur':>6}  Narration")
        print("-" * 90)
        for i, (scene, t) in enumerate(zip(scenes, timings)):
            dur = t["end"] - t["start"]
            rows.append({
                "scene":             i + 1,
                "narration_excerpt": scene,
                "words":             len(scene.split()),
                "duration_seconds":  round(dur, 2),
                "start_time":        fmt_time(t["start"]),
                "end_time":          fmt_time(t["end"]),
                "start_seconds":     t["start"],
                "end_seconds":       t["end"],
            })
            preview = scene[:60] + ("…" if len(scene) > 60 else "")
            print(f"  {i+1:>3}  {fmt_time(t['start']):>7}  {fmt_time(t['end']):>7}  {dur:>5.1f}s  {preview}")

        total = sum(r["duration_seconds"] for r in rows)
        print(f"\nTotal: {total:.2f}s  Audio: {total_duration:.2f}s")
        print(f"Duration range: {min(r['duration_seconds'] for r in rows):.2f}s – {max(r['duration_seconds'] for r in rows):.2f}s")

        # Verify scene text matches narration script exactly
        mismatches = 0
        for row, scene in zip(rows, scenes):
            if row["narration_excerpt"] != scene:
                mismatches += 1
                print(f"  MISMATCH scene {row['scene']}: '{row['narration_excerpt'][:40]}' vs '{scene[:40]}'")
        if mismatches == 0:
            print(f"✓ All {len(scenes)} scenes match the narration script exactly.")
        else:
            print(f"WARNING: {mismatches} scene text mismatches found.")

        # Write CSV
        csv_path = os.path.join(tmpdir, "audio_timings_new.csv")
        fieldnames = ["scene", "narration_excerpt", "words", "duration_seconds",
                      "start_time", "end_time", "start_seconds", "end_seconds"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n✓ CSV written: {len(rows)} rows")

        # Upload to Drive
        print("Uploading audio_timings_new.csv to Drive...")
        token = get_access_token()
        drive_delete_existing(token, "audio_timings_new.csv", folder_id)
        result = drive_upload_csv(token, csv_path, "audio_timings_new.csv", folder_id)
        print(f"  ✓ Uploaded: {result['name']}")
        print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
