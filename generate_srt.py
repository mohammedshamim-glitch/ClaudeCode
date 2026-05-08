#!/usr/bin/env python3
"""
SRT subtitle generator for Monkey Finance episodes.
Uses Whisper-derived timings (audio_timings_new.csv) for exact per-scene timestamps.
Falls back to proportional word count if the CSV is not present.

Usage:
    python3 generate_srt.py <episode_folder_id>
"""

import csv, io, json, os, re, subprocess, sys, tempfile
import requests

# ── Config ─────────────────────────────────────────────────────────────────────
TOKEN_FILE       = "/home/user/ClaudeCode/token.json"
LOCAL_SRT        = "/tmp/narration.srt"
SCRIPT_FILENAME  = "03-narration-script-clean.txt"
AUDIO_FILENAME   = "narration.mp3"
TIMINGS_FILENAME = "audio_timings_new.csv"
OUTPUT_FILENAME  = "narration.srt"

MAX_LINE_CHARS   = 42   # accessibility standard: max chars per subtitle line

# ── OAuth2 ─────────────────────────────────────────────────────────────────────
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

# ── Drive helpers ───────────────────────────────────────────────────────────────
def drive_list_files(token, folder_id):
    files, page_token = [], None
    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed=false",
            "fields": "nextPageToken,files(id,name)",
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

def drive_download(token, file_id, local_path):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"},
        stream=True,
    )
    r.raise_for_status()
    with open(local_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
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
        print(f"  ✓ Deleted existing {f['name']}")

def drive_upload(token, local_path, filename, folder_id):
    with open(local_path, "rb") as f:
        data = f.read()
    metadata = json.dumps({"name": filename, "parents": [folder_id]}).encode()
    boundary = b"srt_boundary_xyz"
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n" +
        metadata + b"\r\n"
        b"--" + boundary + b"\r\n"
        b"Content-Type: text/plain\r\n\r\n" +
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

# ── Audio duration ──────────────────────────────────────────────────────────────
def get_audio_duration(mp3_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", mp3_path],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())

# ── Timestamp formatting ────────────────────────────────────────────────────────
def fmt_srt_time(seconds):
    """Float seconds → SRT timestamp HH:MM:SS,mmm"""
    ms = int(round((seconds % 1) * 1000))
    s  = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ── Line wrapping ───────────────────────────────────────────────────────────────
def wrap_subtitle(text, max_chars=MAX_LINE_CHARS):
    if len(text) <= max_chars:
        return text
    mid = len(text) // 2
    for i in range(mid, len(text)):
        if text[i] == ' ':
            l1, l2 = text[:i].strip(), text[i+1:].strip()
            if len(l1) <= max_chars and len(l2) <= max_chars:
                return f"{l1}\n{l2}"
            break
    for i in range(mid, -1, -1):
        if text[i] == ' ':
            l1, l2 = text[:i].strip(), text[i+1:].strip()
            if len(l1) <= max_chars and len(l2) <= max_chars:
                return f"{l1}\n{l2}"
            break
    return f"{text[:max_chars]}\n{text[max_chars:].strip()}"

# ── SRT builders ────────────────────────────────────────────────────────────────
def build_srt_from_whisper(rows):
    """
    Build SRT from audio_timings_new.csv rows.
    Uses exact Whisper-derived start_seconds / end_seconds.
    """
    rows_sorted = sorted(rows, key=lambda r: int(r["scene"]))
    lines = []
    for idx, row in enumerate(rows_sorted, 1):
        start = float(row["start_seconds"])
        end   = float(row["end_seconds"])
        text  = row["narration_excerpt"].strip()
        wrapped = wrap_subtitle(text)
        lines += [str(idx), f"{fmt_srt_time(start)} --> {fmt_srt_time(end)}", wrapped, ""]
    return "\n".join(lines)

def build_srt_proportional(scenes, total_duration):
    """Fallback: assign timestamps proportionally by word count."""
    total_words = sum(len(t.split()) for t in scenes)
    lines = []
    current = 0.0
    for idx, text in enumerate(scenes, 1):
        wc  = len(text.split())
        dur = (wc / total_words) * total_duration
        end = min(current + dur, total_duration)
        wrapped = wrap_subtitle(text)
        lines += [str(idx), f"{fmt_srt_time(current)} --> {fmt_srt_time(end)}", wrapped, ""]
        current = end
    return "\n".join(lines)

# ── Main ────────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_srt.py <episode_folder_id>")
        sys.exit(1)

    folder_id = sys.argv[1]

    print("Authenticating...")
    token = get_access_token()
    print("  ✓ Authenticated")

    print("Listing episode files...")
    files    = drive_list_files(token, folder_id)
    file_map = {f["name"]: f["id"] for f in files}

    # ── Try Whisper timings first ──────────────────────────────────────────────
    if TIMINGS_FILENAME in file_map:
        print(f"  ✓ Found {TIMINGS_FILENAME} — using exact Whisper timestamps")
        raw = drive_download_text(token, file_map[TIMINGS_FILENAME])
        rows = list(csv.DictReader(io.StringIO(raw)))
        print(f"  ✓ {len(rows)} scenes loaded from Whisper CSV")
        srt_content = build_srt_from_whisper(rows)
        method = "Whisper (exact)"
        scene_count = len(rows)

    # ── Fallback: proportional word count ─────────────────────────────────────
    else:
        print(f"  ⚠ {TIMINGS_FILENAME} not found — falling back to proportional timestamps")
        print(f"    Run generate_timings_whisper.py for more accurate captions")

        if SCRIPT_FILENAME not in file_map:
            print(f"ERROR: '{SCRIPT_FILENAME}' not found in folder.")
            sys.exit(1)
        if AUDIO_FILENAME not in file_map:
            print(f"ERROR: '{AUDIO_FILENAME}' not found. Run TTS first.")
            sys.exit(1)

        script_text = drive_download_text(token, file_map[SCRIPT_FILENAME])
        scenes = [b.strip() for b in re.split(r'\n\s*\n', script_text.strip()) if b.strip()]
        print(f"  ✓ {len(scenes)} scenes parsed from script")

        local_mp3 = "/tmp/srt_narration.mp3"
        print(f"Downloading audio for duration...")
        drive_download(token, file_map[AUDIO_FILENAME], local_mp3)
        total_duration = get_audio_duration(local_mp3)
        print(f"  ✓ Audio: {total_duration:.2f}s")

        srt_content = build_srt_proportional(scenes, total_duration)
        method = "proportional (estimated)"
        scene_count = len(scenes)

    # ── Write and upload ───────────────────────────────────────────────────────
    with open(LOCAL_SRT, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"\nSRT generated: {scene_count} subtitle cards ({method})")

    print(f"Uploading {OUTPUT_FILENAME} to Drive...")
    token = get_access_token()
    drive_delete_existing(token, OUTPUT_FILENAME, folder_id)
    result = drive_upload(token, LOCAL_SRT, OUTPUT_FILENAME, folder_id)
    print(f"  ✓ Uploaded: {result['name']}")
    print(f"  ✓ View:     {result.get('webViewLink', 'n/a')}")
    print()
    print("Next step: upload narration.srt to YouTube Studio → Subtitles")
    print("  Can be done now while the video is still private.")

if __name__ == "__main__":
    main()
