#!/usr/bin/env python3
"""
Generate auto_timings.csv using Gemini audio transcription.

1. Downloads narration.mp3 and narration script from Drive
2. Sends audio + scene list to Gemini 2.0 Flash for timestamp alignment
3. Derives exact start/end time for each scene from the audio
4. Uploads auto_timings.csv to the episode Drive folder
"""

import base64, csv, json, os, re, sys, tempfile, shutil, subprocess, requests, time

TOKEN_FILE     = "/home/user/ClaudeCode/token.json"
GEMINI_API_KEY = "AIzaSyBJRb4hEmBngO4G3UwgidRouvKCkL0gzd0"
GEMINI_MODEL   = "gemini-2.0-flash"

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
def drive_list_all(token, folder_id, mime_filter=None):
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
        for chunk in r.iter_content(8192):
            f.write(chunk)

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
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary.decode()}",
        },
        data=body,
    )
    r.raise_for_status()
    return r.json()

# ── Audio helpers ─────────────────────────────────────────────────────────────
def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())

# ── Scene splitting ───────────────────────────────────────────────────────────
def split_narration(text, n_images):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    total_words = sum(len(s.split()) for s in sentences)
    target = total_words / n_images

    chunks, current, current_words = [], [], 0
    for i, sentence in enumerate(sentences):
        words = len(sentence.split())
        current.append(sentence)
        current_words += words
        slots_filled   = len(chunks)
        slots_left     = n_images - slots_filled
        sentences_left = len(sentences) - i - 1
        if current_words >= target and slots_filled < n_images - 1 and sentences_left >= slots_left - 1:
            chunks.append(" ".join(current))
            current, current_words = [], 0
    if current:
        chunks.append(" ".join(current))
    while len(chunks) > n_images:
        chunks[-2] = chunks[-2] + " " + chunks[-1]
        chunks.pop()
    while len(chunks) < n_images:
        longest = max(range(len(chunks)), key=lambda i: len(chunks[i].split()))
        sents = re.split(r'(?<=[.!?])\s+', chunks[longest])
        if len(sents) < 2:
            chunks.insert(longest + 1, chunks[longest])
        else:
            mid = len(sents) // 2
            chunks[longest] = " ".join(sents[:mid])
            chunks.insert(longest + 1, " ".join(sents[mid:]))
    return chunks

# ── Gemini audio alignment ────────────────────────────────────────────────────
def gemini_get_timestamps(audio_path, chunks, total_duration):
    """
    Send audio + scene list to Gemini. Ask for the start timestamp of each
    scene. Process in batches to stay within token limits.
    """
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()

    # Build numbered scene list
    scene_list = "\n".join(f"{i+1}. {c[:120]}" for i, c in enumerate(chunks))

    prompt = f"""You are a precise audio transcription assistant.

I will give you an audio file containing a narration, and a numbered list of scenes from the narration script.

Your job: for each scene, identify the exact timestamp (in seconds, to 2 decimal places) when that scene's narration STARTS in the audio.

Rules:
- Return ONLY a JSON array of objects with keys "scene" (integer) and "start" (float seconds)
- No extra text, no markdown, no explanation — only the raw JSON array
- Scene 1 always starts at 0.00
- Timestamps must be strictly increasing

SCENES:
{scene_list}

Return JSON only."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "audio/mpeg", "data": audio_b64}},
                {"text": prompt}
            ]
        }],
        "generationConfig": {"temperature": 0}
    }

    print("  Sending audio to Gemini for timestamp alignment...")
    for attempt in range(3):
        r = requests.post(url, json=body, timeout=120)
        if r.ok:
            break
        wait = 2 ** attempt
        print(f"  Retry in {wait}s... ({r.status_code})")
        time.sleep(wait)
    r.raise_for_status()

    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Strip markdown code fences if present
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw)

    data = json.loads(raw)
    print(f"  ✓ Received {len(data)} scene timestamps from Gemini")

    # Build start times list (indexed by scene number)
    start_map = {item["scene"]: float(item["start"]) for item in data}

    # Derive end times: each scene ends when the next starts; last ends at total_duration
    timings = []
    for i in range(len(chunks)):
        scene_num = i + 1
        start = start_map.get(scene_num, None)
        if start is None:
            # Fallback: use previous end
            start = timings[-1]["end"] if timings else 0.0
        next_start = start_map.get(scene_num + 1, total_duration)
        timings.append({"start": start, "end": next_start})

    # Clamp last scene to total_duration
    timings[-1]["end"] = total_duration
    return timings

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

    print("Finding images subfolder...")
    items = drive_list_all(token, folder_id)
    images_folder = next(
        (f for f in items if f["name"].lower() == "images" and "folder" in f["mimeType"]), None
    )
    if not images_folder:
        print("ERROR: No images subfolder found.")
        sys.exit(1)

    image_files = [f for f in drive_list_all(token, images_folder["id"]) if f["mimeType"].startswith("image/")]
    image_files.sort(key=lambda x: x["modifiedTime"])
    n = len(image_files)
    print(f"  ✓ {n} images found")

    narration_script = next(
        (f for f in items if f["name"] in ("narration_script.txt", "03-narration-script-clean.txt")), None
    )
    narration_audio = next((f for f in items if f["name"] == "narration.mp3"), None)
    if not narration_script:
        print("ERROR: narration script not found.")
        sys.exit(1)
    if not narration_audio:
        print("ERROR: narration.mp3 not found.")
        sys.exit(1)

    tmpdir = tempfile.mkdtemp(prefix="mf_whisper_")
    try:
        print("Downloading narration files...")
        script_path = os.path.join(tmpdir, "script.txt")
        audio_path  = os.path.join(tmpdir, "narration.mp3")
        drive_download(token, narration_script["id"], script_path)
        drive_download(token, narration_audio["id"],  audio_path)

        with open(script_path, encoding="utf-8") as f:
            script_text = f.read()

        total_duration = get_audio_duration(audio_path)
        print(f"  ✓ Audio duration: {total_duration:.2f}s")

        chunks = split_narration(script_text, n)
        print(f"  ✓ Script split into {len(chunks)} scene chunks")

        print("\nAligning scenes to audio via Gemini...")
        timings = gemini_get_timestamps(audio_path, chunks, total_duration)

        # Build CSV rows
        rows = []
        print(f"\n{'#':>5}  {'Duration':>8}  {'Start':>7}  {'End':>7}  Narration excerpt")
        print("-" * 80)
        for i, (img, chunk, t) in enumerate(zip(image_files, chunks, timings)):
            dur = t["end"] - t["start"]
            rows.append({
                "scene":             i + 1,
                "image":             img["name"],
                "narration_excerpt": chunk[:80].replace("\n", " ") + ("…" if len(chunk) > 80 else ""),
                "words":             len(chunk.split()),
                "duration_seconds":  round(dur, 2),
                "start_time":        fmt_time(t["start"]),
                "end_time":          fmt_time(t["end"]),
            })
            print(f"  {i+1:>3}  {dur:>8.2f}s  {fmt_time(t['start']):>7}  {fmt_time(t['end']):>7}  {chunk[:40]}")

        total = sum(r["duration_seconds"] for r in rows)
        print(f"\nTotal: {total:.2f}s (audio: {total_duration:.2f}s)")
        print(f"Duration range: {min(r['duration_seconds'] for r in rows):.2f}s – {max(r['duration_seconds'] for r in rows):.2f}s")

        csv_path = os.path.join(tmpdir, "auto_timings.csv")
        fieldnames = ["scene", "image", "narration_excerpt", "words", "duration_seconds", "start_time", "end_time"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print("\nUploading auto_timings.csv to Drive...")
        token = get_access_token()
        drive_delete_existing(token, "auto_timings.csv", folder_id)
        result = drive_upload_csv(token, csv_path, "auto_timings.csv", folder_id)
        print(f"  ✓ Uploaded: {result['name']}")
        print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
