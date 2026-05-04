#!/usr/bin/env python3
"""
SRT subtitle generator for Monkey Finance episodes.
1. Downloads narration_script.txt and narration.mp3 from Drive
2. Splits script into subtitle cards at blank lines (25-word scenes)
3. Calculates timestamps proportionally by word count vs total audio duration
4. Outputs a properly formatted .srt file
5. Uploads narration.srt back to the episode Drive folder

Usage:
    python3 generate_srt.py <episode_folder_id>
"""

import json, os, re, subprocess, sys, tempfile
import requests

# ── Config ─────────────────────────────────────────────────────────────────────
TOKEN_FILE      = "/home/user/ClaudeCode/token.json"
LOCAL_SCRIPT    = "/tmp/srt_narration_script.txt"
LOCAL_MP3       = "/tmp/srt_narration.mp3"
LOCAL_SRT       = "/tmp/narration.srt"
SCRIPT_FILENAME = "03-narration-script-clean.txt"
AUDIO_FILENAME  = "narration.mp3"
OUTPUT_FILENAME = "narration.srt"

# Max characters per subtitle line (accessibility standard)
MAX_LINE_CHARS  = 42

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
    new_tokens = r.json()
    tokens["access_token"] = new_tokens["access_token"]
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
    """Use ffprobe to get duration in seconds."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            mp3_path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())

# ── Script parsing ──────────────────────────────────────────────────────────────
def parse_scenes(text):
    """
    Split the clean narration script into scenes.
    Scenes are separated by blank lines (one per ~25-word block).
    Returns list of (scene_text, word_count) tuples.
    """
    raw_blocks = re.split(r'\n\s*\n', text.strip())
    scenes = []
    for block in raw_blocks:
        cleaned = block.strip()
        if not cleaned:
            continue
        word_count = len(cleaned.split())
        scenes.append((cleaned, word_count))
    return scenes

# ── Timestamp formatting ────────────────────────────────────────────────────────
def fmt_srt_time(seconds):
    """Convert float seconds to SRT timestamp: HH:MM:SS,mmm"""
    ms = int(round((seconds % 1) * 1000))
    s  = int(seconds)
    m  = s // 60
    h  = m // 60
    s  = s % 60
    m  = m % 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ── Line wrapping ───────────────────────────────────────────────────────────────
def wrap_subtitle(text, max_chars=MAX_LINE_CHARS):
    """
    Wrap subtitle text to max 2 lines, max_chars per line.
    Tries to break at a word boundary near the midpoint.
    """
    if len(text) <= max_chars:
        return text
    # Try to split near middle at a space
    mid = len(text) // 2
    # Search forward then backward for a space
    for i in range(mid, len(text)):
        if text[i] == ' ':
            line1, line2 = text[:i].strip(), text[i+1:].strip()
            if len(line1) <= max_chars and len(line2) <= max_chars:
                return f"{line1}\n{line2}"
            break
    for i in range(mid, -1, -1):
        if text[i] == ' ':
            line1, line2 = text[:i].strip(), text[i+1:].strip()
            if len(line1) <= max_chars and len(line2) <= max_chars:
                return f"{line1}\n{line2}"
            break
    # Fallback: hard wrap at max_chars
    return f"{text[:max_chars]}\n{text[max_chars:].strip()}"

# ── SRT generation ──────────────────────────────────────────────────────────────
def build_srt(scenes, total_duration):
    """
    Assign timestamps to each scene proportionally by word count.
    Returns the full SRT file content as a string.
    """
    total_words = sum(wc for _, wc in scenes)
    lines = []
    current_time = 0.0

    for idx, (text, word_count) in enumerate(scenes, 1):
        scene_duration = (word_count / total_words) * total_duration
        # Add a tiny leading gap on first scene
        start = current_time
        end   = current_time + scene_duration
        # Clamp end to total duration
        end = min(end, total_duration)

        wrapped = wrap_subtitle(text)
        lines.append(str(idx))
        lines.append(f"{fmt_srt_time(start)} --> {fmt_srt_time(end)}")
        lines.append(wrapped)
        lines.append("")  # blank line between cards

        current_time = end

    return "\n".join(lines)

# ── Main ────────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_srt.py <episode_folder_id>")
        sys.exit(1)

    folder_id = sys.argv[1]

    print("Authenticating with Google Drive...")
    token = get_access_token()
    print("  ✓ Authenticated")

    print(f"Listing files in folder {folder_id}...")
    files = drive_list_files(token, folder_id)
    file_map = {f["name"]: f["id"] for f in files}

    # Find script
    if SCRIPT_FILENAME not in file_map:
        print(f"ERROR: '{SCRIPT_FILENAME}' not found in folder.")
        print(f"  Found: {list(file_map.keys())}")
        sys.exit(1)

    # Find audio
    if AUDIO_FILENAME not in file_map:
        print(f"ERROR: '{AUDIO_FILENAME}' not found in folder. Run TTS first.")
        sys.exit(1)

    print(f"Downloading {SCRIPT_FILENAME}...")
    drive_download(token, file_map[SCRIPT_FILENAME], LOCAL_SCRIPT)
    with open(LOCAL_SCRIPT, "r") as f:
        script_text = f.read()
    print(f"  ✓ {len(script_text.split())} words")

    print(f"Downloading {AUDIO_FILENAME}...")
    drive_download(token, file_map[AUDIO_FILENAME], LOCAL_MP3)
    print(f"  ✓ Downloaded")

    print("Getting audio duration...")
    total_duration = get_audio_duration(LOCAL_MP3)
    mins = int(total_duration // 60)
    secs = total_duration % 60
    print(f"  ✓ Duration: {mins}m {secs:.1f}s ({total_duration:.2f}s)")

    print("Parsing narration into scenes...")
    scenes = parse_scenes(script_text)
    print(f"  ✓ {len(scenes)} scenes parsed")

    print("Generating SRT timestamps...")
    srt_content = build_srt(scenes, total_duration)
    with open(LOCAL_SRT, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"  ✓ SRT written: {len(scenes)} subtitle cards")

    print(f"Uploading {OUTPUT_FILENAME} to Drive...")
    token = get_access_token()
    drive_delete_existing(token, OUTPUT_FILENAME, folder_id)
    result = drive_upload(token, LOCAL_SRT, OUTPUT_FILENAME, folder_id)
    print(f"  ✓ Uploaded: {result['name']}")
    print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")
    print()
    print("Done. Upload narration.srt to YouTube Studio → Subtitles within 24 hours of publishing.")

if __name__ == "__main__":
    main()
