#!/usr/bin/env python3
"""
Generate auto_timings.csv for a Monkey Finance episode.
- Lists images in the /Images subfolder (sorted by modifiedTime)
- Downloads narration_script.txt and narration.mp3
- Splits audio duration equally across all scenes
- Outputs: scene, image, words, duration_seconds, start_time, end_time
- Uploads auto_timings.csv back to the episode folder
"""

import csv, io, json, os, re, sys, subprocess, tempfile, shutil, requests

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

# ── Audio ─────────────────────────────────────────────────────────────────────
def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())

# ── Timing logic ──────────────────────────────────────────────────────────────
def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]

def split_narration(text, n_images):
    """Split narration into exactly n_images chunks for excerpt display only."""
    sentences = split_into_sentences(text)
    total_words = sum(len(s.split()) for s in sentences)
    target = total_words / n_images

    chunks = []
    current, current_words = [], 0

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
        sents = split_into_sentences(chunks[longest])
        if len(sents) < 2:
            chunks.insert(longest + 1, chunks[longest])
        else:
            mid = len(sents) // 2
            chunks[longest] = " ".join(sents[:mid])
            chunks.insert(longest + 1, " ".join(sents[mid:]))

    return chunks

def fmt_time(seconds):
    m = int(seconds) // 60
    s = seconds - m * 60
    return f"{m:02d}:{s:05.2f}"

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_timings.py <episode_folder_id>")
        sys.exit(1)

    folder_id = sys.argv[1]

    print("Authenticating...")
    token = get_access_token()
    folder_name = drive_get_name(token, folder_id)
    print(f"  ✓ Episode: {folder_name}")

    # Find images subfolder
    print("Finding Images subfolder...")
    items = drive_list_all(token, folder_id)
    images_folder = next(
        (f for f in items if f["name"].lower() == "images" and "folder" in f["mimeType"]), None
    )
    if not images_folder:
        print("ERROR: No Images subfolder found.")
        sys.exit(1)

    # List and sort images
    print("Listing images...")
    image_files = [f for f in drive_list_all(token, images_folder["id"]) if f["mimeType"].startswith("image/")]
    image_files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x["name"])])
    n = len(image_files)
    print(f"  ✓ {n} images found")

    # Find narration files
    narration_script = next(
        (f for f in items if f["name"] in ("narration_script.txt", "03-narration-script-clean.txt")), None
    )
    narration_audio  = next((f for f in items if f["name"] == "narration.mp3"), None)
    if not narration_script:
        print("ERROR: narration_script.txt or 03-narration-script-clean.txt not found.")
        sys.exit(1)
    if not narration_audio:
        print("ERROR: narration.mp3 not found.")
        sys.exit(1)

    tmpdir = tempfile.mkdtemp(prefix="mf_timings_")
    try:
        # Download
        print("Downloading narration files...")
        script_path = os.path.join(tmpdir, "narration_script.txt")
        audio_path  = os.path.join(tmpdir, "narration.mp3")
        drive_download(token, narration_script["id"], script_path)
        drive_download(token, narration_audio["id"],  audio_path)

        with open(script_path, encoding="utf-8") as f:
            script_text = f.read()

        total_duration = get_audio_duration(audio_path)
        print(f"  ✓ Audio duration: {total_duration:.2f}s")

        # Split narration into n chunks for excerpt display
        chunks = split_narration(script_text, n)
        total_words = sum(len(c.split()) for c in chunks)
        print(f"  ✓ Narration split into {len(chunks)} chunks ({total_words} words total)")

        # Equal duration per scene
        equal_dur = total_duration / n
        print(f"  ✓ Equal duration: {equal_dur:.2f}s per scene ({n} scenes)")

        # Build timings — every image gets the same duration
        rows = []
        cursor = 0.0
        for img_idx, img in enumerate(image_files):
            chunk = chunks[img_idx]
            start = cursor
            end   = cursor + equal_dur
            rows.append({
                "scene":             img_idx + 1,
                "image":             img["name"],
                "narration_excerpt": chunk[:80].replace("\n", " ") + ("…" if len(chunk) > 80 else ""),
                "words":             len(chunk.split()),
                "duration_seconds":  round(equal_dur, 2),
                "start_time":        fmt_time(start),
                "end_time":          fmt_time(end),
            })
            cursor = end

        # Write CSV
        csv_path = os.path.join(tmpdir, "auto_timings.csv")
        fieldnames = ["scene", "image", "narration_excerpt", "words", "duration_seconds", "start_time", "end_time"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        # Print preview
        print(f"\n{'#':>5}  {'Duration':>8}  {'Start':>7}  {'End':>7}  Narration excerpt")
        print("-" * 80)
        for r in rows:
            print(f"  {r['scene']:>3}  {r['duration_seconds']:>8.2f}s  {r['start_time']:>7}  {r['end_time']:>7}  {r['narration_excerpt'][:40]}")

        print(f"\nTotal: {sum(r['duration_seconds'] for r in rows):.2f}s (audio: {total_duration:.2f}s)")

        # Upload
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
