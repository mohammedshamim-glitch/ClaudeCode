#!/usr/bin/env python3
"""
Upload a Monkey Finance episode to YouTube with full SEO metadata.

1. Downloads video and 06-seo-metadata.txt from the episode Drive folder
2. Parses title, description, tags, and chapters from the SEO package
3. Uploads video to YouTube via resumable upload
4. Sets all metadata, category, and privacy status

Usage:
    python3 upload_youtube.py <episode_folder_id> [--privacy private|unlisted|public]
"""

import json, os, re, sys, tempfile, shutil, requests, time

TOKEN_FILE   = "/home/user/ClaudeCode/token.json"
VIDEO_MIME   = "video/mp4"
YT_CATEGORY  = "27"   # Education
YT_LANGUAGE  = "en-GB"

# ── Auth ──────────────────────────────────────────────────────────────────────
def load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

def get_drive_token():
    tokens = load_tokens()
    r = requests.get(
        "https://www.googleapis.com/oauth2/v1/tokeninfo",
        params={"access_token": tokens.get("access_token", "")}
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

def get_youtube_token():
    tokens = load_tokens()
    if not tokens.get("youtube_refresh_token"):
        print("ERROR: YouTube not authenticated. Run: python3 setup_youtube_auth.py")
        sys.exit(1)
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":     tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "refresh_token": tokens["youtube_refresh_token"],
        "grant_type":    "refresh_token",
    })
    r.raise_for_status()
    tokens["youtube_access_token"] = r.json()["access_token"]
    save_tokens(tokens)
    return tokens["youtube_access_token"]

# ── Drive helpers ─────────────────────────────────────────────────────────────
def drive_list_all(token, folder_id):
    files, page_token = [], None
    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed=false",
            "fields": "nextPageToken,files(id,name,mimeType)",
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
    total = int(r.headers.get("Content-Length", 0))
    downloaded = 0
    with open(local_path, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r  Downloading... {pct:.0f}% ({downloaded//1024//1024}MB/{total//1024//1024}MB)", end="", flush=True)
    print()

# ── SEO parser ────────────────────────────────────────────────────────────────
def is_separator(line):
    stripped = line.strip()
    return len(stripped) >= 5 and all(c in '━═─' for c in stripped)

def parse_seo_metadata(text):
    """Parse 06-seo-metadata.txt — structure is ━━━\nSECTION\n━━━\ncontent."""
    lines = text.split('\n')
    sections = {}
    current_section = None
    content_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if is_separator(line):
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and not is_separator(lines[j]):
                name_line = lines[j].strip().upper()
                k = j + 1
                if k < len(lines) and is_separator(lines[k]):
                    if current_section and content_lines:
                        sections[current_section] = '\n'.join(content_lines).strip()
                    current_section = name_line
                    content_lines = []
                    i = k + 1
                    continue
        if current_section is not None:
            content_lines.append(line)
        i += 1

    if current_section and content_lines:
        sections[current_section] = '\n'.join(content_lines).strip()

    result = {"title": "", "description": "", "tags": []}

    titles_block = sections.get('TITLES', '')
    m = re.search(r'PRIMARY[^\n]*\n([^\n\[]+)', titles_block, re.IGNORECASE)
    if m:
        result["title"] = re.sub(r'\s*\[\d+ characters?\]', '', m.group(1)).strip()

    desc_block = sections.get('DESCRIPTION', '')
    result["description"] = re.split(r'\n---\n|\n#[A-Z]', desc_block)[0].strip()

    for key in sections:
        if 'TAG' in key and 'HASHTAG' not in key:
            tags = [t.strip().lstrip('#') for t in re.split(r'[\n,]+', sections[key]) if t.strip()]
            result["tags"] = [t for t in tags if len(t) > 1]
            break

    for key in sections:
        if 'CHAPTER' in key:
            if result["description"]:
                result["description"] += "\n\n" + sections[key]
            break

    return result

# ── YouTube upload ─────────────────────────────────────────────────────────────
def youtube_resumable_upload(yt_token, video_path, metadata):
    """Upload video using YouTube resumable upload protocol."""
    file_size = os.path.getsize(video_path)

    # Step 1: Initiate resumable upload session
    body = {
        "snippet": {
            "title":                 metadata["title"],
            "description":           metadata["description"],
            "tags":                  metadata["tags"],
            "categoryId":            YT_CATEGORY,
            "defaultLanguage":       YT_LANGUAGE,
            "defaultAudioLanguage":  YT_LANGUAGE,
        },
        "status": {
            "privacyStatus":             metadata.get("privacy", "private"),
            "selfDeclaredMadeForKids":   False,
        },
    }

    r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization":       f"Bearer {yt_token}",
            "Content-Type":        "application/json",
            "X-Upload-Content-Type": VIDEO_MIME,
            "X-Upload-Content-Length": str(file_size),
        },
        json=body,
    )
    r.raise_for_status()
    upload_url = r.headers["Location"]
    print(f"  ✓ Upload session created")

    # Step 2: Upload video in chunks
    chunk_size = 8 * 1024 * 1024  # 8MB chunks
    uploaded = 0

    with open(video_path, "rb") as f:
        while uploaded < file_size:
            chunk = f.read(chunk_size)
            end = uploaded + len(chunk) - 1
            headers = {
                "Authorization":  f"Bearer {yt_token}",
                "Content-Type":   VIDEO_MIME,
                "Content-Range":  f"bytes {uploaded}-{end}/{file_size}",
                "Content-Length": str(len(chunk)),
            }
            for attempt in range(4):
                r = requests.put(upload_url, headers=headers, data=chunk, timeout=120)
                if r.status_code in (200, 201, 308):
                    break
                wait = 2 ** attempt
                print(f"\n  Upload error {r.status_code}, retry in {wait}s...")
                time.sleep(wait)

            uploaded += len(chunk)
            pct = uploaded / file_size * 100
            print(f"\r  Uploading... {pct:.0f}% ({uploaded//1024//1024}MB/{file_size//1024//1024}MB)", end="", flush=True)

            if r.status_code in (200, 201):
                print()
                return r.json()

    print()
    return r.json()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 upload_youtube.py <episode_folder_id> [--privacy private|unlisted|public]")
        sys.exit(1)

    folder_id = sys.argv[1]
    privacy   = "private"
    if "--privacy" in sys.argv:
        idx = sys.argv.index("--privacy")
        if idx + 1 < len(sys.argv):
            privacy = sys.argv[idx + 1]

    print("Authenticating...")
    drive_token = get_drive_token()
    yt_token    = get_youtube_token()
    folder_name = drive_get_name(drive_token, folder_id)
    print(f"  ✓ Episode: {folder_name}")
    print(f"  ✓ Privacy: {privacy}")

    print("Listing episode files...")
    items = drive_list_all(drive_token, folder_id)

    seo_file    = next((f for f in items if f["name"] == "06-seo-metadata.txt"), None)
    video_folder = next((f for f in items if f["name"].lower() == "video" and "folder" in f["mimeType"]), None)

    # Look for video in episode root first, then in Video subfolder
    video_file = next((f for f in items if f["mimeType"] == "video/mp4"), None)
    if not video_file and video_folder:
        sub_items  = drive_list_all(drive_token, video_folder["id"])
        video_file = next((f for f in sub_items if f["mimeType"] == "video/mp4"), None)

    if not video_file:
        print("ERROR: No .mp4 video file found in episode folder or Video subfolder")
        sys.exit(1)
    if not seo_file:
        print("ERROR: 06-seo-metadata.txt not found in episode folder")
        sys.exit(1)

    print(f"  ✓ Video: {video_file['name']}")
    print(f"  ✓ SEO:   {seo_file['name']}")

    tmpdir = tempfile.mkdtemp(prefix="mf_yt_")
    try:
        print("\nDownloading SEO metadata...")
        seo_path   = os.path.join(tmpdir, "seo.txt")
        video_path = os.path.join(tmpdir, "video.mp4")

        r = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{seo_file['id']}?alt=media",
            headers={"Authorization": f"Bearer {drive_token}"}
        )
        r.raise_for_status()
        seo_text = r.content.decode('utf-8')
        print("  ✓ SEO metadata downloaded")

        metadata = parse_seo_metadata(seo_text)
        metadata["privacy"] = privacy

        if not metadata["title"]:
            print("ERROR: Could not parse title from 06-seo-metadata.txt")
            sys.exit(1)

        print(f"\n  Title:  {metadata['title']}")
        print(f"  Tags:   {len(metadata['tags'])} tags")
        print(f"  Desc:   {len(metadata['description'])} chars")

        print(f"\nDownloading video ({video_file['name']})...")
        drive_download(drive_token, video_file["id"], video_path)
        size_mb = os.path.getsize(video_path) / 1024 / 1024
        print(f"  ✓ {size_mb:.1f}MB downloaded")

        print("\nUploading to YouTube...")
        result = youtube_resumable_upload(yt_token, video_path, metadata)

        video_id  = result.get("id", "unknown")
        yt_url    = f"https://www.youtube.com/watch?v={video_id}"
        yt_studio = f"https://studio.youtube.com/video/{video_id}/edit"

        print(f"\n{'='*60}")
        print(f"  ✓ Upload complete!")
        print(f"  ✓ Video ID:    {video_id}")
        print(f"  ✓ Watch URL:   {yt_url}")
        print(f"  ✓ Studio URL:  {yt_studio}")
        print(f"  ✓ Privacy:     {privacy}")
        print(f"{'='*60}\n")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
