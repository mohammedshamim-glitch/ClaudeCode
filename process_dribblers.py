#!/usr/bin/env python3
"""
Top 10 Dribblers — smart Shorts pipeline
- Two-pass scene detection (major chapters + fine cuts)
- OCR player identification from title cards
- Smart grouping: 30-55s, never mid-scene
- Player name overlay (yellow, 5s), mxm watermark, fade out last 5s
"""

import json, re, subprocess, requests, os
from pathlib import Path

TOKEN_FILE    = '/home/user/ClaudeCode/token.json'
SHORTS_ROOT   = '10puXRPV_81umNFxxirV3zzF3x6XnvlML'
COMPLETED_ID  = '1GjBbF-WlYtMHw0K4LTqY_tplvN_-4d9A'
DRIVE_FILE_ID = '1cwhLmLCWPu0pllRzr_jTY2TYMKLLCbf6'
SRC           = Path('/home/user/ClaudeCode/mxm_shorts/downloads/Top-10-Dribblers.mp4')
CLIPS_DIR     = Path('/home/user/ClaudeCode/mxm_shorts/clips/dribblers_v2')
PROCESSED_DIR = Path('/home/user/ClaudeCode/mxm_shorts/processed')
FRAMES_DIR    = Path('/home/user/ClaudeCode/mxm_shorts/frames_ocr')

CLIP_MAX     = 55
CLIP_MIN     = 30
THRESH_MAJOR = 0.55
THRESH_FINE  = 0.25
FONT         = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# Words to ignore in OCR output — not player names
IGNORE_WORDS = {
    'subscribe', 'like', 'follow', 'share', 'youtube', 'channel',
    'goals', 'skills', 'edit', 'highlights', 'compilation', 'best',
    'top', 'hd', 'official', 'football', 'soccer', 'premier', 'league',
    'champions', 'watch', 'more', 'video', 'click', 'here', 'link',
    'instagram', 'twitter', 'tiktok', 'reels',
}

# ── Auth ─────────────────────────────────────────────────────────────────────

def get_drive_token():
    with open(TOKEN_FILE) as f:
        t = json.load(f)
    r = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': t['client_id'], 'client_secret': t['client_secret'],
        'refresh_token': t['drive_refresh_token'], 'grant_type': 'refresh_token'})
    r.raise_for_status()
    token = r.json()['access_token']
    t['drive_access_token'] = token
    with open(TOKEN_FILE, 'w') as f:
        json.dump(t, f, indent=2)
    return token

# ── Video utils ───────────────────────────────────────────────────────────────

def get_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
        capture_output=True, text=True)
    return float(r.stdout.strip())


def detect_scenes(src, threshold):
    r = subprocess.run(['ffmpeg', '-i', str(src),
        '-vf', f"select='gt(scene,{threshold})',showinfo",
        '-vsync', 'vfr', '-f', 'null', '-'],
        capture_output=True, text=True)
    times = [0.0]
    for line in r.stderr.splitlines():
        if 'pts_time:' in line:
            m = re.search(r'pts_time:([\d.]+)', line)
            if m:
                times.append(float(m.group(1)))
    duration = get_duration(src)
    times.append(duration)
    return sorted(set(times)), duration


def extract_frame(src, timestamp, out_path):
    subprocess.run(['ffmpeg', '-y', '-ss', str(timestamp), '-i', str(src),
        '-vframes', '1', '-q:v', '2', str(out_path)], capture_output=True)

# ── OCR ───────────────────────────────────────────────────────────────────────

def ocr_player_name(frame_path):
    """Run OCR on frame, return a likely player name or None."""
    try:
        import easyocr
        reader = easyocr.Reader(['en'], verbose=False)
        results = reader.readtext(str(frame_path))
        # Collect all text chunks with decent confidence
        chunks = [r[1].strip() for r in results if r[2] > 0.4]
        # Filter: looking for proper-noun-style text (2+ chars, not in ignore list)
        candidates = []
        for chunk in chunks:
            words = chunk.split()
            clean_words = [w for w in words
                           if w.lower() not in IGNORE_WORDS
                           and len(w) > 2
                           and not w.isdigit()
                           and re.match(r"[A-Za-zÀ-ÿ']", w)]
            if clean_words:
                candidates.append(' '.join(clean_words))
        if not candidates:
            return None
        # Prefer longer candidates (more likely to be a full name)
        best = max(candidates, key=len)
        # Must be at least 4 chars to be a real name
        return best if len(best) >= 4 else None
    except Exception as e:
        print(f'    OCR error: {e}')
        return None


def identify_chapter_player(src, chapter_start, chapter_end):
    """Try OCR on a few frames near the chapter start to find a player name."""
    FRAMES_DIR.mkdir(exist_ok=True)
    # Check 3 frames: at the transition, +1s, +2s
    for offset in [0.1, 0.5, 1.0, 1.5, 2.0]:
        ts = min(chapter_start + offset, chapter_end - 0.5)
        frame_path = FRAMES_DIR / f'ocr_{chapter_start:.0f}_{offset:.1f}.jpg'
        extract_frame(src, ts, frame_path)
        name = ocr_player_name(frame_path)
        if name:
            return name
    return None

# ── Chapter building ──────────────────────────────────────────────────────────

def build_chapters(major_times, duration):
    """Turn major transition timestamps into (start, end) chapter pairs."""
    chapters = []
    for i in range(len(major_times) - 1):
        start, end = major_times[i], major_times[i + 1]
        chapters.append((start, end))
    return chapters


def merge_short_chapters(chapters, min_dur=30):
    """Merge consecutive chapters that are shorter than min_dur."""
    if not chapters:
        return chapters
    merged = [list(chapters[0])]
    for start, end in chapters[1:]:
        dur = merged[-1][1] - merged[-1][0]
        if dur < min_dur:
            merged[-1][1] = end  # extend previous chapter
        else:
            merged.append([start, end])
    # Handle last chapter if still too short
    if len(merged) > 1 and (merged[-1][1] - merged[-1][0]) < min_dur:
        merged[-2][1] = merged[-1][1]
        merged.pop()
    return [tuple(c) for c in merged]


def split_long_chapter(start, end, fine_times, clip_max=55, clip_min=30):
    """Split a chapter >55s using fine-grained cuts. Never cut mid-scene."""
    segments = []
    seg_start = start
    # Fine times within this chapter only
    within = [t for t in fine_times if start < t < end]
    candidates = [start] + within + [end]

    i = 1
    while i < len(candidates):
        length = candidates[i] - seg_start
        if length <= clip_max:
            # Can we go further and still be in range?
            if i + 1 < len(candidates) and (candidates[i + 1] - seg_start) <= clip_max:
                i += 1
                continue
            # This is the best cut point
            if length >= clip_min:
                segments.append((seg_start, candidates[i]))
                seg_start = candidates[i]
            i += 1
        else:
            # Gone over — cut at previous candidate
            prev = candidates[i - 1]
            if prev > seg_start + clip_min:
                segments.append((seg_start, prev))
                seg_start = prev
            else:
                # No good cut found — take what we have up to clip_max
                segments.append((seg_start, seg_start + clip_max))
                seg_start += clip_max
            i += 1

    # Final tail
    tail = end - seg_start
    if tail >= clip_min:
        segments.append((seg_start, end))
    elif segments:
        # Absorb tail into last segment if it won't push over clip_max
        last_s, last_e = segments[-1]
        if end - last_s <= clip_max:
            segments[-1] = (last_s, end)

    return segments

# ── Processing ────────────────────────────────────────────────────────────────

def cut_clip(src, start, end, out_path):
    if out_path.exists():
        return
    subprocess.run(['ffmpeg', '-y', '-ss', str(start), '-i', str(src),
        '-t', str(end - start), '-c', 'copy', str(out_path)],
        capture_output=True)


def process_clip(raw_path, out_path, player_name):
    """Crop 9:16, watermark, player name overlay, fade out last 5s."""
    # Get dimensions
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(raw_path)],
        capture_output=True, text=True)
    w, h = map(int, r.stdout.strip().split(','))
    duration = get_duration(raw_path)

    # Crop to 9:16
    crop_w = min(int(h * 9 / 16), w)
    crop_h = min(int(w * 16 / 9), h) if crop_w == w else h
    x_off = (w - crop_w) // 2
    y_off = (h - crop_h) // 2

    fade_start = max(0, duration - 5)
    safe_name = player_name.replace("'", "\\'")

    vf_parts = [
        f"crop={crop_w}:{crop_h}:{x_off}:{y_off}",
        "scale=1080:1920",
        # Player name — yellow, centred, top 12%, first 5s
        f"drawtext=text='{safe_name}':fontfile={FONT}:fontsize=56"
        f":fontcolor=yellow:x=(w-tw)/2:y=h*0.12"
        f":box=1:boxcolor=black@0.4:boxborderw=8"
        f":enable='between(t,0,5)'",
        # mxm watermark — white, bottom-right, always
        f"drawtext=text='mxm':fontfile={FONT}:fontsize=72"
        f":fontcolor=white@0.7:x=w-tw-40:y=h-th-40",
        # Fade to black
        f"fade=t=out:st={fade_start:.2f}:d=5",
    ]

    subprocess.run([
        'ffmpeg', '-y', '-i', str(raw_path),
        '-vf', ','.join(vf_parts),
        '-af', f'afade=t=out:st={fade_start:.2f}:d=5',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
        str(out_path)
    ], capture_output=True)


def save_to_drive(path, filename, folder_id, token):
    size = path.stat().st_size
    r = requests.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'X-Upload-Content-Type': 'video/mp4'},
        json={'name': filename, 'parents': [folder_id]})
    r.raise_for_status()
    with open(path, 'rb') as f:
        r2 = requests.put(r.headers['Location'],
            headers={'Content-Type': 'video/mp4', 'Content-Length': str(size)}, data=f)
    if r2.status_code in (200, 201):
        return r2.json().get('id')
    return None


def get_or_create_folder(name, parent_id, token):
    r = requests.get('https://www.googleapis.com/drive/v3/files',
        params={'q': f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false",
                'fields': 'files(id)'},
        headers={'Authorization': f'Bearer {token}'})
    files = r.json().get('files', [])
    if files:
        return files[0]['id']
    r2 = requests.post('https://www.googleapis.com/drive/v3/files',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]})
    r2.raise_for_status()
    return r2.json()['id']


def move_to_completed(file_id, token):
    r = requests.get(f'https://www.googleapis.com/drive/v3/files/{file_id}',
        params={'fields': 'parents'}, headers={'Authorization': f'Bearer {token}'})
    parents = ','.join(r.json().get('parents', []))
    requests.patch(f'https://www.googleapis.com/drive/v3/files/{file_id}',
        params={'addParents': COMPLETED_ID, 'removeParents': parents, 'fields': 'id'},
        headers={'Authorization': f'Bearer {token}'})

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    for d in [CLIPS_DIR, PROCESSED_DIR, FRAMES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    print('=== Top 10 Dribblers — Smart Shorts Pipeline ===\n')
    token = get_drive_token()

    # Pass 1: major transitions
    print(f'Pass 1 — major scene detection (threshold {THRESH_MAJOR})...')
    major_times, duration = detect_scenes(SRC, THRESH_MAJOR)
    print(f'  → {len(major_times)-2} major transitions | duration: {duration:.0f}s ({duration/60:.1f} min)')

    # Pass 2: fine cuts
    print(f'Pass 2 — fine scene detection (threshold {THRESH_FINE})...')
    fine_times, _ = detect_scenes(SRC, THRESH_FINE)
    print(f'  → {len(fine_times)-2} fine cuts detected\n')

    # Build and merge chapters
    raw_chapters = build_chapters(major_times, duration)
    chapters = merge_short_chapters(raw_chapters, min_dur=CLIP_MIN)
    print(f'Chapters after merging: {len(chapters)}')

    # Identify players via OCR and split long chapters
    segments = []
    for i, (ch_start, ch_end) in enumerate(chapters):
        ch_dur = ch_end - ch_start
        print(f'\n  Chapter {i+1}: {ch_start:.0f}s → {ch_end:.0f}s ({ch_dur:.0f}s)')

        # OCR
        player = identify_chapter_player(SRC, ch_start, ch_end)
        if player:
            print(f'    👤 Player identified: {player}')
        else:
            player = 'Football Skills'
            print(f'    👤 No name found — using "Football Skills"')

        # Split if needed
        if ch_dur <= CLIP_MAX:
            segments.append((ch_start, ch_end, player))
        else:
            print(f'    ✂ Chapter too long ({ch_dur:.0f}s) — splitting...')
            splits = split_long_chapter(ch_start, ch_end, fine_times)
            for j, (s, e) in enumerate(splits):
                label = f'{player} Part {j+1}' if len(splits) > 1 else player
                segments.append((s, e, label))
                print(f'      → {s:.0f}s–{e:.0f}s ({e-s:.0f}s) [{label}]')

    print(f'\n{len(segments)} Shorts to create\n')

    # Create Drive folder
    folder_id = get_or_create_folder('Top 10 Dribblers 2025-26', SHORTS_ROOT, token)
    print(f'Drive folder ready\n')

    # Cut, process, upload
    player_counters = {}
    for i, (start, end, player) in enumerate(segments, 1):
        base = re.sub(r'[^A-Za-z0-9 ]', '', player).replace(' ', '_')
        count = player_counters.get(player, 0) + 1
        player_counters[player] = count
        raw_name  = f'raw_{i:03d}_{base}.mp4'
        out_name  = f'{base}_short_{count:03d}.mp4'
        raw_path  = CLIPS_DIR / raw_name
        out_path  = PROCESSED_DIR / out_name

        print(f'[{i}/{len(segments)}] {player} ({end-start:.0f}s)')
        cut_clip(SRC, start, end, raw_path)

        if not out_path.exists():
            process_clip(raw_path, out_path, player)

        fid = save_to_drive(out_path, out_name, folder_id, token)
        print(f'  ✓ Saved to Drive: {out_name}' if fid else f'  ✗ Drive save failed')

        if i % 10 == 0:
            token = get_drive_token()

    # Move source to Completed
    move_to_completed(DRIVE_FILE_ID, token)
    print(f'\n✓ Source moved to Completed')
    print(f'\n=== Done — {len(segments)} Shorts in Drive ===')
    print(f'⚠️  Awaiting confirmation before YouTube upload.')

if __name__ == '__main__':
    main()
