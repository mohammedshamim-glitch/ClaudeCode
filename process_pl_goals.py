#!/usr/bin/env python3
"""
Premier League Goals 2020-2025 — Full pipeline:
  Stage 1: Full edit — add music + rotating hook text → Drive + YouTube Jun 10 12:00 BST
  Stage 2: Shorts (up to 10) → Drive + YouTube Jun 19-28 17:00 BST
"""

import json, re, subprocess, requests, time
from pathlib import Path

TOKEN_FILE   = '/home/user/ClaudeCode/token.json'
FONT         = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
DRIVE_ROOT   = '10puXRPV_81umNFxxirV3zzF3x6XnvlML'

EDIT_SRC     = Path('/home/user/ClaudeCode/mxm_shorts/processed/PL_Goals_2020_2025_Edit.mp4')
RAW_SRC      = Path('/home/user/ClaudeCode/mxm_shorts/downloads/PL_Goals_2020_2025.mp4')
FINAL_VIDEO  = Path('/home/user/ClaudeCode/mxm_shorts/processed/PL_Goals_2020_2025_Final.mp4')
THUMBNAIL    = Path('/home/user/ClaudeCode/mxm_shorts/processed/PL_Goals_thumbnail.jpg')
SHORTS_DIR   = Path('/home/user/ClaudeCode/mxm_shorts/processed/pl_goals')
CLIPS_DIR    = Path('/home/user/ClaudeCode/mxm_shorts/clips/pl_goals')
MUSIC_FILES  = [
    Path('/home/user/ClaudeCode/mxm_shorts/music/upbeat_background_1.mp3'),
    Path('/home/user/ClaudeCode/mxm_shorts/music/upbeat_background_2.mp3'),
]

CLIP_MAX     = 40
CLIP_MIN     = 30
THRESH_MAJOR = 0.55
THRESH_FINE  = 0.25
MAX_SHORTS   = 10
TRIM_START   = 8.0   # seconds trimmed from raw source start
TRIM_END     = 10.0  # seconds trimmed from raw source end

FULL_PUBLISH  = '2026-06-10T11:00:00Z'  # 12:00 BST
SHORT_PUBLISH = [f'2026-06-{d:02d}T16:00:00Z' for d in range(19, 29)]  # 17:00 BST

FULL_TITLE = "Premier League’s Best Goals 2020–2025 \U0001f525 5 Years of Pure Magic"
FULL_DESC  = (
    "5 years of the most jaw-dropping Premier League goals — all in one place.\n"
    "From stunning long-rangers to clinical finishes, this is the best of 2020–2025.\n\n"
    "\U0001f514 Subscribe for daily football clips — @mxmballers\n\n"
    "#PremierLeague #Football #Goals #FootballHighlights #EPL #BestGoals "
    "#PremierLeagueGoals #FootballSkills #mxmballers #Soccer"
)
FULL_TAGS = [
    'Premier League', 'Football', 'Goals', 'Best Goals', 'Premier League Goals',
    'EPL', 'Football Highlights', 'Soccer', 'mxmballers', 'Top Goals',
    'Premier League Highlights', 'Football 2025', 'Best Football Goals',
]

SHORT_TITLES = [
    "Premier_League_Goals_That_Broke_The_Internet",
    "When_PL_Strikers_Were_Simply_Unstoppable",
    "Goals_Only_Premier_League_Players_Score",
    "The_PL_Goal_Nobody_Saw_Coming",
    "Premier_League_At_Its_Absolute_Best",
    "When_The_Premier_League_Was_Electric",
    "Defenders_Stood_No_Chance",
    "Premier_League_Pure_Class",
    "The_Strike_That_Silenced_Everyone",
    "Premier_League_Magic_2020_to_2025",
]

SHORT_DESC = (
    "\U0001f525 Premier League goals you won’t believe!\n\n"
    "#Shorts #Football #PremierLeague #Goals #EPL #mxmballers #FootballHighlights"
)
SHORT_TAGS = ['Shorts', 'Football', 'PremierLeague', 'Goals', 'EPL',
              'mxmballers', 'FootballHighlights', 'BestGoals']

HOOKS = [
    "Wait for it...",
    "Watch this...",
    "No way...",
    "Here it comes...",
    "Do not blink...",
    "Pure class...",
    "Unbelievable...",
    "What a goal!",
    "Absolute rocket!",
    "Top bins!",
]


def get_youtube_token():
    with open(TOKEN_FILE) as f:
        t = json.load(f)
    r = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': t['client_id'], 'client_secret': t['client_secret'],
        'refresh_token': t['youtube_refresh_token'], 'grant_type': 'refresh_token'})
    r.raise_for_status()
    token = r.json()['access_token']
    t['youtube_access_token'] = token
    with open(TOKEN_FILE, 'w') as f:
        json.dump(t, f, indent=2)
    return token


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


def get_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
        capture_output=True, text=True)
    return float(r.stdout.strip())


def detect_scenes(src, threshold):
    r = subprocess.run(['ffmpeg', '-i', str(src),
        '-vf', f"select='gt(scene,{threshold})',showinfo",
        '-vsync', 'vfr', '-f', 'null', '-'], capture_output=True, text=True)
    times = [0.0]
    for line in r.stderr.splitlines():
        if 'pts_time:' in line:
            m = re.search(r'pts_time:([\d.]+)', line)
            if m:
                times.append(float(m.group(1)))
    duration = get_duration(src)
    times.append(duration)
    return sorted(set(times)), duration


def build_segments(major_times, fine_times):
    chapters = [(major_times[i], major_times[i+1]) for i in range(len(major_times)-1)]
    merged = [list(chapters[0])]
    for start, end in chapters[1:]:
        if merged[-1][1] - merged[-1][0] < CLIP_MIN:
            merged[-1][1] = end
        else:
            merged.append([start, end])
    if len(merged) > 1 and (merged[-1][1] - merged[-1][0]) < CLIP_MIN:
        merged[-2][1] = merged[-1][1]
        merged.pop()
    chapters = [tuple(c) for c in merged]
    segments = []
    for ch_start, ch_end in chapters:
        if ch_end - ch_start <= CLIP_MAX:
            segments.append((ch_start, ch_end))
        else:
            within = [t for t in fine_times if ch_start < t < ch_end]
            candidates = [ch_start] + within + [ch_end]
            seg_start = ch_start
            i = 1
            while i < len(candidates):
                length = candidates[i] - seg_start
                if length <= CLIP_MAX:
                    if i + 1 < len(candidates) and (candidates[i+1] - seg_start) <= CLIP_MAX:
                        i += 1; continue
                    if length >= CLIP_MIN:
                        segments.append((seg_start, candidates[i]))
                        seg_start = candidates[i]
                    i += 1
                else:
                    prev = candidates[i-1]
                    if prev > seg_start + CLIP_MIN:
                        segments.append((seg_start, prev)); seg_start = prev
                    else:
                        segments.append((seg_start, seg_start + CLIP_MAX)); seg_start += CLIP_MAX
                    i += 1
            tail = ch_end - seg_start
            if tail >= CLIP_MIN:
                segments.append((seg_start, ch_end))
            elif segments:
                ls, le = segments[-1]
                if ch_end - ls <= CLIP_MAX:
                    segments[-1] = (ls, ch_end)
    return segments


def build_full_edit():
    if FINAL_VIDEO.exists():
        print('  ↩ Full edit already processed')
        return
    duration = get_duration(EDIT_SRC)
    # Hook every 55s starting at t=45, show for 3s
    hook_filters = []
    idx = 0
    t = 45
    while t + 3 < duration:
        text = HOOKS[idx % len(HOOKS)]
        escaped = text.replace("'", "\\'").replace(':', '\\:')
        hook_filters.append(
            f"drawtext=text='{escaped}':fontfile={FONT}:fontsize=26:fontcolor=white"
            f":x=(w-tw)/2:y=h*0.45:box=1:boxcolor=black@0.5:boxborderw=6"
            f":enable='between(t,{t},{t+3})'"
        )
        idx += 1
        t += 55

    vf = ','.join(hook_filters)
    cmd = [
        'ffmpeg', '-y',
        '-i', str(EDIT_SRC),
        '-stream_loop', '-1', '-i', str(MUSIC_FILES[0]),
        '-vf', vf,
        '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest', '-movflags', '+faststart',
        str(FINAL_VIDEO)
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise Exception(f'ffmpeg failed: {result.stderr[-500:].decode()}')
    print(f'  ✓ Final edit: {FINAL_VIDEO.stat().st_size // 1024 // 1024}MB, {len(hook_filters)} hooks')


def make_thumbnail():
    if THUMBNAIL.exists():
        print('  ↩ Thumbnail already exists')
        return
    vf = (
        "scale=1280:720,"
        "drawbox=x=0:y=590:w=1280:h=130:color=black@0.6:t=fill,"
        f"drawtext=text='Best Premier League Goals 2020-2025':fontfile={FONT}"
        ":fontsize=42:fontcolor=white:x=(w-tw)/2:y=608"
        ":shadowcolor=black@0.8:shadowx=2:shadowy=2,"
        f"drawtext=text='5 Years of Pure Magic':fontfile={FONT}"
        ":fontsize=28:fontcolor=white@0.9:x=(w-tw)/2:y=664"
        ":shadowcolor=black@0.8:shadowx=2:shadowy=2"
    )
    subprocess.run([
        'ffmpeg', '-y', '-ss', '20', '-i', str(FINAL_VIDEO),
        '-vf', vf, '-vframes', '1', str(THUMBNAIL)
    ], capture_output=True, check=True)
    print(f'  ✓ Thumbnail: {THUMBNAIL.stat().st_size // 1024}KB')


def process_short(raw_path, out_path, hook_text, music_path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(raw_path)],
        capture_output=True, text=True)
    w, h = map(int, r.stdout.strip().split(','))
    crop_w = min(int(h * 9 / 16), w)
    crop_h = h if crop_w < w else min(int(w * 16 / 9), h)
    x_off = (w - crop_w) // 2
    y_off = (h - crop_h) // 2
    escaped = hook_text.replace("'", "\\'").replace(':', '\\:')
    vf = (
        f"crop={crop_w}:{crop_h}:{x_off}:{y_off},scale=1080:1920,"
        f"drawtext=text='mxm':fontfile={FONT}:fontsize=72:fontcolor=white@0.7:x=w-tw-40:y=h-th-40,"
        f"drawtext=text='{escaped}':fontfile={FONT}:fontsize=56:fontcolor=white"
        f":x=(w-tw)/2:y=h*0.45:box=1:boxcolor=black@0.5:boxborderw=10:enable='between(t,15,18)'"
    )
    subprocess.run([
        'ffmpeg', '-y', '-i', str(raw_path),
        '-stream_loop', '-1', '-i', str(music_path),
        '-vf', vf, '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart',
        str(out_path)
    ], capture_output=True, check=True)


def get_or_create_folder(name, parent_id, token):
    r = requests.get('https://www.googleapis.com/drive/v3/files', params={
        'q': f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false",
        'fields': 'files(id)'}, headers={'Authorization': f'Bearer {token}'})
    files = r.json().get('files', [])
    if files:
        return files[0]['id']
    r2 = requests.post('https://www.googleapis.com/drive/v3/files',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]})
    r2.raise_for_status()
    return r2.json()['id']


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
    return r2.json().get('id') if r2.status_code in (200, 201) else None


def upload_youtube(path, title, description, tags, publish_at, token, thumb_path=None):
    size = path.stat().st_size
    r = requests.post(
        'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(size)},
        json={
            'snippet': {
                'title': title, 'description': description, 'tags': tags,
                'categoryId': '17', 'defaultLanguage': 'en-GB', 'defaultAudioLanguage': 'en-GB',
            },
            'status': {
                'privacyStatus': 'private', 'publishAt': publish_at,
                'selfDeclaredMadeForKids': False,
            },
        })
    r.raise_for_status()
    with open(path, 'rb') as f:
        r2 = requests.put(r.headers['Location'],
            headers={'Content-Type': 'video/mp4', 'Content-Length': str(size)}, data=f)
    if r2.status_code not in (200, 201):
        raise Exception(f'Upload failed: {r2.status_code} {r2.text[:200]}')
    video_id = r2.json()['id']
    if thumb_path and thumb_path.exists():
        mime = 'image/jpeg' if thumb_path.suffix.lower() in ('.jpg', '.jpeg') else 'image/png'
        r3 = requests.post(
            f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}&uploadType=media',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': mime,
                     'Content-Length': str(thumb_path.stat().st_size)},
            data=thumb_path.read_bytes())
        if r3.status_code not in (200, 201):
            print(f'  ⚠ Thumbnail failed: {r3.status_code}')
    return video_id


def main():
    SHORTS_DIR.mkdir(parents=True, exist_ok=True)
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    print('=== PL Goals 2020-2025 Pipeline ===\n')

    # ── Stage 1: Full edit ────────────────────────────────────────────────
    print('Stage 1 — Adding music + hook overlays to full edit...')
    build_full_edit()

    print('Stage 1 — Generating thumbnail...')
    make_thumbnail()

    drive_token = get_drive_token()
    full_folder = get_or_create_folder('PL Goals 2020-2025', DRIVE_ROOT, drive_token)

    print('Stage 1 — Uploading full edit to Drive...')
    fid = save_to_drive(FINAL_VIDEO, 'PL_Goals_2020_2025_Final.mp4', full_folder, drive_token)
    drive_link = f'https://drive.google.com/file/d/{fid}/view' if fid else 'FAILED'
    print(f'  {"✓ " + drive_link if fid else "✗ Drive upload failed"}')

    print('Stage 1 — Uploading full edit to YouTube...')
    yt_token = get_youtube_token()
    vid = upload_youtube(FINAL_VIDEO, FULL_TITLE, FULL_DESC, FULL_TAGS,
                         FULL_PUBLISH, yt_token, THUMBNAIL)
    print(f'  ✓ Scheduled 10 Jun 12:00 BST — https://www.youtube.com/watch?v={vid}')

    # ── Stage 2: Shorts ───────────────────────────────────────────────────
    print('\nStage 2 — Scene detection on raw source...')
    major_times, raw_duration = detect_scenes(RAW_SRC, THRESH_MAJOR)
    print(f'  → {len(major_times)-2} major transitions | {raw_duration:.0f}s')
    fine_times, _ = detect_scenes(RAW_SRC, THRESH_FINE)
    print(f'  → {len(fine_times)-2} fine cuts')

    # Normalise times to the trimmed edit window
    edit_end = raw_duration - TRIM_END
    adj_major = sorted(set(
        [0.0] + [t - TRIM_START for t in major_times if TRIM_START < t < edit_end] +
        [edit_end - TRIM_START]
    ))
    adj_fine = sorted(set(
        [0.0] + [t - TRIM_START for t in fine_times if TRIM_START < t < edit_end] +
        [edit_end - TRIM_START]
    ))

    all_segs = build_segments(adj_major, adj_fine)
    segments = all_segs[:MAX_SHORTS]
    print(f'  → {len(all_segs)} segments total, processing first {len(segments)}\n')

    short_folder = get_or_create_folder('PL Goals 2020-2025 Shorts', DRIVE_ROOT, drive_token)

    for i, (start, end) in enumerate(segments, 1):
        music    = MUSIC_FILES[(i - 1) % len(MUSIC_FILES)]
        hook     = HOOKS[(i - 1) % len(HOOKS)]
        raw_path = CLIPS_DIR / f'raw_{i:03d}.mp4'
        stem     = SHORT_TITLES[i-1] if i <= len(SHORT_TITLES) else f'PL_Goal_{i}'
        out_path = SHORTS_DIR / f'{stem}.mp4'
        publish  = SHORT_PUBLISH[i-1]
        title    = f"{stem.replace('_', ' ')} #Shorts #Football #PremierLeague"
        bst_day  = int(publish[8:10])
        bst_hour = int(publish[11:13]) + 1

        print(f'[{i}/{len(segments)}] {stem.replace("_"," ")} ({end-start:.0f}s) — "{hook}"')

        if not out_path.exists():
            raw_start = start + TRIM_START
            subprocess.run(['ffmpeg', '-y', '-ss', str(raw_start), '-i', str(RAW_SRC),
                '-t', str(end - start), '-c', 'copy', str(raw_path)], capture_output=True)
            process_short(raw_path, out_path, hook, music)
            print('  ✓ Encoded')
        else:
            print('  ↩ Already encoded')

        fid = save_to_drive(out_path, f'{stem}.mp4', short_folder, drive_token)
        print(f'  {"✓ Drive saved" if fid else "✗ Drive failed"}')

        vid = upload_youtube(out_path, title, SHORT_DESC, SHORT_TAGS, publish, yt_token)
        print(f'  ✓ {bst_day} Jun {bst_hour:02d}:00 BST — https://www.youtube.com/shorts/{vid}')

        time.sleep(2)

    print(f'\n=== Done — full video + {len(segments)} Shorts ===')
    print(f'Full video: 10 Jun 12:00 BST')
    print(f'Shorts: 19-28 Jun 17:00 BST')


if __name__ == '__main__':
    main()
