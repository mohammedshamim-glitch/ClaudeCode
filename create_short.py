#!/usr/bin/env python3
"""
create_short.py — Build and upload a YouTube Short from a Monkey Finance episode.

Usage:
    python3 create_short.py <folder_id> <youtube_video_id> "<episode_title>" [--schedule YYYY-MM-DDTHH:MM:SSZ] [--dry-run]

Auto-selects segments from audio_timings_new.csv (or falls back to proportional
timing if no CSV exists). Builds 1080x1920 vertical Short with blur background,
uploads to Drive, then schedules on YouTube.
"""

import argparse, csv, io, json, os, re, shutil, subprocess, sys, tempfile, time
import requests

# ── Auth helpers ────────────────────────────────────────────────────────────

def load_tokens():
    with open(os.path.join(os.path.dirname(__file__), "token.json")) as f:
        return json.load(f)

def refresh_token(tokens, refresh_key="refresh_token"):
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "refresh_token": tokens[refresh_key],
        "grant_type": "refresh_token",
    })
    r.raise_for_status()
    return r.json()["access_token"]

# ── Drive helpers ────────────────────────────────────────────────────────────

def list_folder(folder_id, drive_headers):
    resp = requests.get("https://www.googleapis.com/drive/v3/files",
        params={"q": f"'{folder_id}' in parents and trashed=false",
                "fields": "files(id,name,mimeType,size)", "pageSize": 50},
        headers=drive_headers).json()
    return resp.get("files", [])

def download_drive_file(file_id, dest_path, drive_headers, label=""):
    with requests.get(f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
            headers=drive_headers, stream=True) as r:
        r.raise_for_status()
        total = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)
                total += len(chunk)
    print(f"  ✓ Downloaded {label} ({total // 1024 // 1024}MB)")

def upload_to_drive(file_path, filename, folder_id, drive_headers):
    metadata = json.dumps({"name": filename, "parents": [folder_id]})
    with open(file_path, "rb") as f:
        data = f.read()
    boundary = "short_upload_boundary"
    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{metadata}\r\n"
        f"--{boundary}\r\nContent-Type: video/mp4\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--".encode()
    resp = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
        headers={**drive_headers, "Content-Type": f"multipart/related; boundary={boundary}"},
        data=body,
    ).json()
    if "id" not in resp:
        raise RuntimeError(f"Drive upload failed: {resp}")
    return resp["id"], resp.get("webViewLink", "")

# ── Segment selection ────────────────────────────────────────────────────────

REVEAL_KEYWORDS = [
    r"^here'?s what", r"^so what does", r"^here'?s the thing",
    r"^here'?s the real", r"^the truth is", r"^the real",
    r"^one:", r"^two:", r"^three:", r"^first,", r"^lesson",
    r"^what (can|does) (we|this|all of) (take|tell|mean)",
    r"^stripped (right )?back", r"^what this really means",
]

def pick_segments_from_csv(csv_content, target_total=57.0):
    """Pick hook/reveal/closure segments from audio_timings_new.csv."""
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    if not rows:
        return None

    def s(row): return float(row.get("start_seconds", row.get("start", 0)))
    def e(row): return float(row.get("end_seconds", row.get("end", 0)))

    total_dur = e(rows[-1])

    # Hook: first 2 scenes (up to ~16s)
    hook_start = 0.0
    hook_end = min(e(rows[1]) if len(rows) > 1 else e(rows[0]), 17.0)

    # Reveal: look for keyword match around 45-75% of video
    reveal_row = None
    window_start = total_dur * 0.45
    window_end   = total_dur * 0.75
    for row in rows:
        if s(row) < window_start or s(row) > window_end:
            continue
        text = row.get("narration_excerpt", "").strip().lower()
        for pat in REVEAL_KEYWORDS:
            if re.match(pat, text):
                reveal_row = row
                break
        if reveal_row:
            break

    # Fall back to 55% mark if no keyword match
    if not reveal_row:
        target = total_dur * 0.55
        reveal_row = min(rows, key=lambda r: abs(s(r) - target))

    reveal_start = s(reveal_row)
    # Reveal: 16-22s from that point
    reveal_end = min(reveal_start + 22.0, e(reveal_row) + 14.0)
    # Snap to nearest row end within the range
    for row in rows:
        if s(row) >= reveal_start and e(row) <= reveal_start + 23.0:
            reveal_end = e(row)

    reveal_dur = reveal_end - reveal_start
    closure_target = target_total - (hook_end - hook_start) - reveal_dur

    # Closure: find a complete-sentence end near 80-90% mark
    window_start_c = total_dur * 0.78
    window_end_c   = total_dur * 0.92
    closure_candidates = [
        r for r in rows
        if s(r) >= window_start_c and e(r) <= window_end_c
        and r.get("narration_excerpt", "").rstrip().endswith(".")
    ]

    if closure_candidates:
        # Pick a starting row near the target window
        best = min(closure_candidates, key=lambda r: abs(s(r) - (total_dur * 0.83)))
        closure_start = s(best)
        # Build closure by extending only within the target duration window
        target_window_end = closure_start + closure_target + 5.0  # 5s slack
        closure_end = e(best)
        for row in rows:
            if s(row) > closure_start and e(row) <= target_window_end:
                closure_end = e(row)
                if row.get("narration_excerpt", "").rstrip().endswith("."):
                    break  # stop at first complete sentence within window
        # Hard cap
        closure_end = min(closure_end, closure_start + closure_target + 5.0)
    else:
        # Proportional fallback for closure
        closure_start = total_dur * 0.82
        closure_end   = min(closure_start + closure_target, total_dur - 1.0)

    actual_total = (hook_end - hook_start) + (reveal_end - reveal_start) + (closure_end - closure_start)

    print(f"  Hook:    {hook_start:.1f}s → {hook_end:.1f}s  ({hook_end - hook_start:.1f}s)")
    print(f"  Reveal:  {reveal_start:.1f}s → {reveal_end:.1f}s  ({reveal_end - reveal_start:.1f}s)")
    print(f"  Closure: {closure_start:.1f}s → {closure_end:.1f}s  ({closure_end - closure_start:.1f}s)")
    print(f"  Total:   {actual_total:.1f}s")

    return hook_start, hook_end, reveal_start, reveal_end, closure_start, closure_end

def pick_segments_proportional(mp4_path, target_total=57.0):
    """Proportional segment selection when no CSV available."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", mp4_path],
        capture_output=True, text=True
    )
    total_dur = float(result.stdout.strip())

    # For very short videos (< 90s), just use the whole thing — it's basically already a Short
    if total_dur < 90:
        print(f"  Source is {total_dur:.0f}s — using as-is (no segment splitting)")
        return 0.0, total_dur - 0.5, None, None, None, None  # signal: use full video

    hook_start   = 0.0
    hook_end     = min(15.0, max(10.0, total_dur * 0.06))
    reveal_start = total_dur * 0.55
    reveal_end   = reveal_start + 19.0
    closure_start = total_dur * 0.82
    closure_end   = min(closure_start + 23.0, total_dur - 1.0)

    actual = (hook_end - hook_start) + (reveal_end - reveal_start) + (closure_end - closure_start)
    print(f"  (Proportional — no CSV available, total video: {total_dur:.0f}s)")
    print(f"  Hook:    {hook_start:.1f}s → {hook_end:.1f}s  ({hook_end - hook_start:.1f}s)")
    print(f"  Reveal:  {reveal_start:.1f}s → {reveal_end:.1f}s  ({reveal_end - reveal_start:.1f}s)")
    print(f"  Closure: {closure_start:.1f}s → {closure_end:.1f}s  ({closure_end - closure_start:.1f}s)")
    print(f"  Total:   {actual:.1f}s")

    return hook_start, hook_end, reveal_start, reveal_end, closure_start, closure_end

# ── Short builder ────────────────────────────────────────────────────────────

def build_short(mp4_path, hook_start, hook_end, reveal_start, reveal_end,
                closure_start, closure_end, out_path):
    if reveal_start is None:
        # Full-video mode: just reformat to vertical (video < 90s)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(hook_start), "-to", str(hook_end), "-i", mp4_path,
            "-filter_complex",
            "[0:v]split=2[bg][fg];"
            "[bg]scale=-2:1920,crop=1080:1920:(iw-1080)/2:0,boxblur=25:5[blurred];"
            "[fg]scale=1080:608[small];"
            "[blurred][small]overlay=(W-w)/2:(H-h)/2[vout]",
            "-map", "[vout]", "-map", "0:a",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            out_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(hook_start),    "-to", str(hook_end),    "-i", mp4_path,
            "-ss", str(reveal_start),  "-to", str(reveal_end),  "-i", mp4_path,
            "-ss", str(closure_start), "-to", str(closure_end), "-i", mp4_path,
            "-filter_complex",
            "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[vraw][aout];"
            "[vraw]split=2[bg][fg];"
            "[bg]scale=-2:1920,crop=1080:1920:(iw-1080)/2:0,boxblur=25:5[blurred];"
            "[fg]scale=1080:608[small];"
            "[blurred][small]overlay=(W-w)/2:(H-h)/2[vout]",
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            out_path,
        ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr[-500:]}")
    # Verify output
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration,size",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", out_path],
        capture_output=True, text=True
    ).stdout.strip().split("\n")
    print(f"  ✓ Short built: {out_path}")
    for line in probe:
        print(f"    {line}")

# ── YouTube upload ───────────────────────────────────────────────────────────

def youtube_upload_short(short_path, title, description, tags, publish_at, yt_headers):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",
            "defaultLanguage": "en-GB",
            "defaultAudioLanguage": "en-GB",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": False,
        },
    }
    file_size = os.path.getsize(short_path)
    init_resp = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={**yt_headers, "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4",
                 "X-Upload-Content-Length": str(file_size)},
        json=body,
    )
    if init_resp.status_code != 200:
        raise RuntimeError(f"YouTube init failed: {init_resp.status_code} {init_resp.text[:300]}")
    upload_uri = init_resp.headers["Location"]
    with open(short_path, "rb") as f:
        data = f.read()
    up = requests.put(upload_uri,
        headers={**yt_headers, "Content-Type": "video/mp4",
                 "Content-Length": str(len(data))},
        data=data)
    if up.status_code not in (200, 201):
        raise RuntimeError(f"YouTube upload failed: {up.status_code} {up.text[:300]}")
    return up.json()["id"]

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder_id")
    ap.add_argument("youtube_video_id")
    ap.add_argument("episode_title")
    ap.add_argument("short_title")
    ap.add_argument("--schedule", required=True, help="ISO UTC e.g. 2026-06-05T15:00:00Z")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tokens = load_tokens()
    drive_token = refresh_token(tokens, "refresh_token")
    drive_headers = {"Authorization": f"Bearer {drive_token}"}

    print(f"\n{'='*60}")
    print(f"Episode: {args.episode_title}")
    print(f"Folder:  {args.folder_id}")
    print(f"YT ID:   {args.youtube_video_id}")
    print(f"Sched:   {args.schedule}")
    print(f"{'='*60}\n")

    # Find MP4 and CSV in folder
    files = list_folder(args.folder_id, drive_headers)
    # Exclude short_preview files — always use the source video
    mp4_file = next((f for f in files
                     if "video/" in f["mimeType"]
                     and "short" not in f["name"].lower()), None)
    csv_file = next((f for f in files if "timings" in f["name"]), None)

    if not mp4_file:
        print("ERROR: No source MP4 found in folder (short_preview files excluded). Skipping.")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        mp4_path = os.path.join(tmpdir, "source.mp4")
        print(f"Downloading MP4 ({int(mp4_file.get('size',0))//1024//1024}MB)...")
        download_drive_file(mp4_file["id"], mp4_path, drive_headers, "MP4")

        # Get actual video duration for validation
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", mp4_path],
            capture_output=True, text=True)
        actual_duration = float(probe.stdout.strip())
        print(f"  Source video duration: {actual_duration:.1f}s")

        # Pick segments
        print("\nSelecting segments...")
        segs = None
        if csv_file:
            print(f"  Using CSV: {csv_file['name']}")
            # Google Sheets files need export endpoint; plain CSV uses alt=media
            csv_mime = csv_file.get("mimeType", "")
            if "spreadsheet" in csv_mime or "google-apps" in csv_mime:
                r = requests.get(
                    f"https://www.googleapis.com/drive/v3/files/{csv_file['id']}/export",
                    params={"mimeType": "text/csv"}, headers=drive_headers)
            else:
                r = requests.get(
                    f"https://www.googleapis.com/drive/v3/files/{csv_file['id']}?alt=media",
                    headers=drive_headers)
            csv_text = r.content.decode("utf-8")
            # Validate CSV has proper timestamps and matches video
            try:
                test_rows = list(csv.DictReader(io.StringIO(csv_text)))
                if test_rows:
                    last_end = float(test_rows[-1].get("end_seconds", test_rows[-1].get("end", 0)))
                    if last_end < 10 or last_end > actual_duration * 1.5:
                        print(f"  CSV timestamps mismatch (CSV end={last_end:.1f}s vs video={actual_duration:.1f}s) — using proportional")
                        csv_text = None
            except Exception as ex:
                print(f"  CSV parse error: {ex} — using proportional")
                csv_text = None
            if csv_text:
                segs = pick_segments_from_csv(csv_text)

        if not segs:
            print("  No CSV — using proportional timing")
            segs = pick_segments_proportional(mp4_path)

        hook_s, hook_e, rev_s, rev_e, clo_s, clo_e = segs

        # Hard-cap all segments to actual video duration (skip if full-video mode)
        hook_e = min(hook_e, actual_duration - 0.5)
        if rev_s is not None:
            rev_s  = min(rev_s,  actual_duration - 5.0)
            rev_e  = min(rev_e,  actual_duration - 0.5)
            clo_s  = min(clo_s,  actual_duration - 5.0)
            clo_e  = min(clo_e,  actual_duration - 0.5)

        if rev_s is not None:
            total_short = (hook_e - hook_s) + (rev_e - rev_s) + (clo_e - clo_s)
            print(f"\n  Final segments (capped to {actual_duration:.1f}s source):")
            print(f"  Hook:    {hook_s:.1f}→{hook_e:.1f}  ({hook_e-hook_s:.1f}s)")
            print(f"  Reveal:  {rev_s:.1f}→{rev_e:.1f}  ({rev_e-rev_s:.1f}s)")
            print(f"  Closure: {clo_s:.1f}→{clo_e:.1f}  ({clo_e-clo_s:.1f}s)")
            print(f"  → Short total: {total_short:.1f}s")
        else:
            print(f"\n  Full-video mode: 0.0→{hook_e:.1f}s ({hook_e:.1f}s)")

        if args.dry_run:
            print("\n[DRY RUN] — no files built or uploaded.")
            return

        # Build Short
        short_path = os.path.join(tmpdir, "short_preview_v1.mp4")
        print("\nBuilding Short...")
        build_short(mp4_path, hook_s, hook_e, rev_s, rev_e, clo_s, clo_e, short_path)

        # Upload to Drive
        print("\nUploading to Drive...")
        file_id, link = upload_to_drive(short_path, "short_preview_v1.mp4",
                                         args.folder_id, drive_headers)
        print(f"  ✓ Drive: {link}")

        # Upload to YouTube
        yt_token = refresh_token(tokens, "youtube_refresh_token")
        yt_headers = {"Authorization": f"Bearer {yt_token}"}

        # Mandatory channel check
        ch = requests.get("https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet", "mine": True}, headers=yt_headers).json()
        channel_name = ch["items"][0]["snippet"]["title"]
        assert channel_name == "Monkey See Money", f"WRONG CHANNEL: {channel_name}"
        print(f"\nChannel verified: {channel_name}")

        description = (
            f"{args.episode_title.split('—')[0].strip()} explained in under a minute.\n\n"
            f"Watch the full video 👇\n"
            f"https://www.youtube.com/watch?v={args.youtube_video_id}\n\n"
            f"Subscribe for new UK finance videos every week 👇\n"
            f"https://www.youtube.com/@MonkeySeeMoney\n\n"
            f"#PersonalFinanceUK #MoneyTips #MonkeySeeMoney #UKFinance #Shorts"
        )
        tags = ["personal finance UK", "money tips UK", "UK finance explained",
                "Monkey See Money", "financial education UK", "money shorts"]

        print(f"\nUploading to YouTube (scheduled: {args.schedule})...")
        video_id = youtube_upload_short(short_path, args.short_title, description,
                                         tags, args.schedule, yt_headers)
        print(f"  ✓ YouTube: https://www.youtube.com/watch?v={video_id}")
        print(f"\n✅ Done! Pin comment after going live:")
        print(f'   "Full video here 👉 https://www.youtube.com/watch?v={args.youtube_video_id}"')

if __name__ == "__main__":
    main()
