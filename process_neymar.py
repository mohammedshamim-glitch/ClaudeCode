#!/usr/bin/env python3
"""
Neymar Prime in Barcelona — Shorts pipeline
Scene detect → 30-40s clips → 9:16 + hook + music → Drive + YouTube Jun 29 onwards
"""

import json, re, subprocess, requests, time
from pathlib import Path

TOKEN_FILE   = '/home/user/ClaudeCode/token.json'
FONT         = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
DRIVE_ROOT   = '10puXRPV_81umNFxxirV3zzF3x6XnvlML'

SRC          = Path('/home/user/ClaudeCode/mxm_shorts/downloads/Neymar_Prime_Barcelona_1080p.mp4')
CLIPS_DIR    = Path('/home/user/ClaudeCode/mxm_shorts/clips/neymar')
SHORTS_DIR   = Path('/home/user/ClaudeCode/mxm_shorts/processed/neymar')
MUSIC_FILES  = [
    Path('/home/user/ClaudeCode/mxm_shorts/music/upbeat_background_1.mp3'),
    Path('/home/user/ClaudeCode/mxm_shorts/music/upbeat_background_2.mp3'),
]

CLIP_MAX     = 40
CLIP_MIN     = 30
THRESH_MAJOR = 0.55
THRESH_FINE  = 0.25
MAX_SHORTS   = 10

SHORT_PUBLISH = [
    '2026-06-29T16:00:00Z',
    '2026-06-30T16:00:00Z',
    '2026-07-01T16:00:00Z',
    '2026-07-02T16:00:00Z',
    '2026-07-03T16:00:00Z',
    '2026-07-04T16:00:00Z',
    '2026-07-05T16:00:00Z',
    '2026-07-06T16:00:00Z',
    '2026-07-07T16:00:00Z',
    '2026-07-08T16:00:00Z',
]

SHORT_TITLES = [
    "Neymar_At_His_Absolute_Best",
    "When_Neymar_Was_Unplayable",
    "Neymar_Made_It_Look_Too_Easy",
    "The_Skill_Only_Neymar_Can_Do",
    "Neymar_Prime_Was_Something_Else",
    "Defenders_Had_No_Answer_For_Neymar",
    "Neymar_Barcelona_Pure_Magic",
    "When_Neymar_Was_The_Best_In_The_World",
    "Neymar_Skills_That_Break_The_Internet",
    "Nobody_Could_Stop_Neymar",
]

HOOKS = [
    "Wait for it...",
    "Watch this...",
    "No way...",
    "Here it comes...",
    "Do not blink...",
    "Pure class...",
    "Unbelievable...",
    "What a skill!",
    "Absolutely filthy!",
    "Top bins!",
]

SHORT_DESC = (
    "\U0001f525 Neymar at his absolute best!\n\n"
    "#Shorts #Neymar #Football #Barcelona #Skills #mxmballers #FootballSkills"
)
SHORT_TAGS = ['Shorts', 'Neymar', 'Football', 'Barcelona', 'Skills',
              'mxmballers', 'FootballSkills', 'NeymarSkills', 'LaLiga']


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


def upload_youtube(path, title, description, tags, publish_at, token):
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
    return r2.json()['id']


def main():
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    SHORTS_DIR.mkdir(parents=True, exist_ok=True)

    print('=== Neymar Prime Barcelona — Shorts Pipeline ===\n')

    print('Scene detection...')
    major_times, duration = detect_scenes(SRC, THRESH_MAJOR)
    print(f'  → {len(major_times)-2} major transitions | {duration:.0f}s')
    fine_times, _ = detect_scenes(SRC, THRESH_FINE)
    print(f'  → {len(fine_times)-2} fine cuts')

    all_segs = build_segments(major_times, fine_times)
    segments = all_segs[:MAX_SHORTS]
    print(f'  → {len(all_segs)} segments total, processing first {len(segments)}\n')

    drive_token = get_drive_token()
    folder_id = get_or_create_folder('Neymar Prime Barcelona Shorts', DRIVE_ROOT, drive_token)
    yt_token = get_youtube_token()

    for i, (start, end) in enumerate(segments, 1):
        music    = MUSIC_FILES[(i - 1) % len(MUSIC_FILES)]
        hook     = HOOKS[(i - 1) % len(HOOKS)]
        raw_path = CLIPS_DIR / f'raw_{i:03d}.mp4'
        stem     = SHORT_TITLES[i-1] if i <= len(SHORT_TITLES) else f'Neymar_Skill_{i}'
        out_path = SHORTS_DIR / f'{stem}.mp4'
        publish  = SHORT_PUBLISH[i-1]
        title    = f"{stem.replace('_', ' ')} #Shorts #Football #Neymar"
        bst_day  = publish[8:10]
        bst_mon  = 'Jun' if publish[5:7] == '06' else 'Jul'
        bst_hour = int(publish[11:13]) + 1

        print(f'[{i}/{len(segments)}] {stem.replace("_"," ")} ({end-start:.0f}s) — "{hook}"')

        if not out_path.exists():
            subprocess.run(['ffmpeg', '-y', '-ss', str(start), '-i', str(SRC),
                '-t', str(end - start), '-c', 'copy', str(raw_path)], capture_output=True)
            process_short(raw_path, out_path, hook, music)
            print('  ✓ Encoded')
        else:
            print('  ↩ Already encoded')

        fid = save_to_drive(out_path, f'{stem}.mp4', folder_id, drive_token)
        print(f'  {"✓ Drive saved" if fid else "✗ Drive failed"}')

        vid = upload_youtube(out_path, title, SHORT_DESC, SHORT_TAGS, publish, yt_token)
        print(f'  ✓ {bst_day} {bst_mon} {bst_hour:02d}:00 BST — https://www.youtube.com/shorts/{vid}')

        time.sleep(2)

    print(f'\n=== Done — {len(segments)} Neymar Shorts ===')
    print(f'Scheduled: 29 Jun – 08 Jul, 17:00 BST')


if __name__ == '__main__':
    main()
