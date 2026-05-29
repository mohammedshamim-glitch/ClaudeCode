#!/usr/bin/env python3
"""Lionel Messi - Top 30 Goals — Shorts pipeline"""

import json, re, subprocess, requests
from pathlib import Path

TOKEN_FILE    = '/home/user/ClaudeCode/token.json'
SHORTS_ROOT   = '10puXRPV_81umNFxxirV3zzF3x6XnvlML'
COMPLETED_ID  = '1GjBbF-WlYtMHw0K4LTqY_tplvN_-4d9A'
DRIVE_FILE_ID = '1VjFiUan-7oJFXy4XKBCCCJ1XzlQRIVjS'
FOLDER_NAME   = 'Lionel Messi - Top 30 Goals'
FONT          = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MUSIC         = Path('/home/user/ClaudeCode/mxm_shorts/music/upbeat_background_1.mp3')
SRC           = Path('/home/user/ClaudeCode/mxm_shorts/downloads/Lionel_Messi_Top_30_Goals.mp4')
CLIPS_DIR     = Path('/home/user/ClaudeCode/mxm_shorts/clips/messi')
PROCESSED_DIR = Path('/home/user/ClaudeCode/mxm_shorts/processed/messi')

CLIP_MAX     = 40
CLIP_MIN     = 30
THRESH_MAJOR = 0.55
THRESH_FINE  = 0.25

SHORT_TITLES = [
    "Messi_Makes_It_Look_Effortless",
    "The_Goal_Only_Messi_Scores",
    "Messi_Leaves_The_Keeper_No_Chance",
    "When_Messi_Decided_He_Was_Scoring",
    "Only_Messi_Can_Do_This",
    "Messi_At_His_Absolute_Best",
    "The_Strike_That_Defines_Messi",
    "Messi_Magic_In_Full_Flow",
    "Defenders_Cant_Stop_Messi",
    "Messi_Does_It_Again",
    "Pure_Messi_Brilliance",
    "The_Messi_Goal_Nobody_Saw_Coming",
]

# Rotated per clip — keeps each Short feeling fresh
HOOKS = [
    "Wait for it...",
    "Watch closely...",
    "No way...",
    "Here it comes...",
    "Do not blink...",
    "Pure class...",
    "Watch this...",
    "Unbelievable...",
]


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


def process_clip(raw_path, out_path, hook_text):
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
        '-stream_loop', '-1', '-i', str(MUSIC),
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


def move_to_completed(file_id, token):
    r = requests.get(f'https://www.googleapis.com/drive/v3/files/{file_id}',
        params={'fields': 'parents'}, headers={'Authorization': f'Bearer {token}'})
    parents = ','.join(r.json().get('parents', []))
    requests.patch(f'https://www.googleapis.com/drive/v3/files/{file_id}',
        params={'addParents': COMPLETED_ID, 'removeParents': parents, 'fields': 'id'},
        headers={'Authorization': f'Bearer {token}'})


def main():
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print('=== Lionel Messi — Top 30 Goals Shorts Pipeline ===\n')
    token = get_drive_token()

    # Download if needed
    if not SRC.exists():
        print('Downloading from Drive...')
        r = requests.get(f'https://www.googleapis.com/drive/v3/files/{DRIVE_FILE_ID}?alt=media',
            headers={'Authorization': f'Bearer {token}'}, stream=True)
        r.raise_for_status()
        with open(SRC, 'wb') as f:
            for chunk in r.iter_content(1024 * 1024):
                f.write(chunk)
        print(f'  ✓ Downloaded {SRC.stat().st_size // 1024 // 1024}MB')
    else:
        print(f'  ↩ Already downloaded')

    print(f'\nPass 1 — major transitions (threshold {THRESH_MAJOR})...')
    major_times, duration = detect_scenes(SRC, THRESH_MAJOR)
    print(f'  → {len(major_times)-2} major transitions | {duration:.0f}s ({duration/60:.1f} min)')

    print(f'Pass 2 — fine cuts (threshold {THRESH_FINE})...')
    fine_times, _ = detect_scenes(SRC, THRESH_FINE)
    print(f'  → {len(fine_times)-2} fine cuts\n')

    segments = build_segments(major_times, fine_times)
    print(f'Total segments: {len(segments)}')
    for i, (s, e) in enumerate(segments, 1):
        print(f'  Clip {i}: {s:.0f}s → {e:.0f}s ({e-s:.0f}s)')

    folder_id = get_or_create_folder(FOLDER_NAME, SHORTS_ROOT, token)
    print(f'\nDrive folder ready\n')

    for i, (start, end) in enumerate(segments, 1):
        hook = HOOKS[(i - 1) % len(HOOKS)]
        raw_path = CLIPS_DIR / f'raw_{i:03d}.mp4'
        out_name = f'{SHORT_TITLES[i-1]}.mp4' if i <= len(SHORT_TITLES) else f'Messi_Goal_{i}.mp4'
        out_path = PROCESSED_DIR / out_name

        print(f'[{i}/{len(segments)}] {out_name.replace(".mp4","").replace("_"," ")} ({end-start:.0f}s) — "{hook}"')
        if out_path.exists():
            print(f'  ↩ Already processed')
            continue
        subprocess.run(['ffmpeg', '-y', '-ss', str(start), '-i', str(SRC),
            '-t', str(end - start), '-c', 'copy', str(raw_path)], capture_output=True)
        process_clip(raw_path, out_path, hook)

        fid = save_to_drive(out_path, out_name, folder_id, token)
        print(f'  ✓ Saved to Drive' if fid else f'  ✗ Drive save failed')

    move_to_completed(DRIVE_FILE_ID, token)
    print(f'\n✓ Source moved to Completed')
    print(f'\n=== Done — {len(segments)} Shorts in Drive ===')
    print(f'Review the clips, then confirm before uploading to YouTube.')


if __name__ == '__main__':
    main()
