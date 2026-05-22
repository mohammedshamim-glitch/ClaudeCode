#!/usr/bin/env python3
"""
The BEST Showboats in Premier League History — Shorts pipeline
"""

import json, re, subprocess, requests, shutil
from pathlib import Path

TOKEN_FILE    = '/home/user/ClaudeCode/token.json'
SHORTS_ROOT   = '10puXRPV_81umNFxxirV3zzF3x6XnvlML'
COMPLETED_ID  = '1GjBbF-WlYtMHw0K4LTqY_tplvN_-4d9A'
DRIVE_FILE_ID = '1E4SH7LKqOK8xlMHePUXprAVH8ENJxUWO'
FOLDER_NAME   = 'The BEST Showboats in Premier League History'
SRC           = Path('/home/user/ClaudeCode/mxm_shorts/downloads/The_BEST_Showboats_in_Premier_League_history_____1080p.MPEG-4.mp4')
CLIPS_DIR     = Path('/home/user/ClaudeCode/mxm_shorts/clips/showboats')
PROCESSED_DIR = Path('/home/user/ClaudeCode/mxm_shorts/processed/showboats')
FONT          = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

CLIP_MAX      = 40
CLIP_MIN      = 30
THRESH_MAJOR  = 0.55
THRESH_FINE   = 0.25

# Set to None to process all clips, or an int to process first N only
PROCESS_LIMIT = None

SHORT_TITLES = [
    "The_Showboat_That_Made_The_Crowd_Go_Crazy",
    "When_Players_Forgot_They_Were_Playing_Football",
    "The_Skill_Nobody_Asked_For_But_Everyone_Loved",
    "Premier_League_Showboating_At_Its_Absolute_Peak",
    "When_Showing_Off_Becomes_An_Art_Form",
    "Defenders_Didnt_Know_Whether_To_Laugh_Or_Cry",
    "The_Most_Unnecessary_But_Beautiful_Skill_Ever",
    "When_The_Crowd_Forgot_About_The_Score",
    "Pure_Entertainment_Football_At_Its_Finest",
    "Premier_League_Magic_Nobody_Talks_About_Enough",
    "When_Football_Became_Pure_Theatre",
    "The_Flair_That_Made_Everyone_Stop_And_Stare",
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
                        i += 1
                        continue
                    if length >= CLIP_MIN:
                        segments.append((seg_start, candidates[i]))
                        seg_start = candidates[i]
                    i += 1
                else:
                    prev = candidates[i-1]
                    if prev > seg_start + CLIP_MIN:
                        segments.append((seg_start, prev))
                        seg_start = prev
                    else:
                        segments.append((seg_start, seg_start + CLIP_MAX))
                        seg_start += CLIP_MAX
                    i += 1
            tail = ch_end - seg_start
            if tail >= CLIP_MIN:
                segments.append((seg_start, ch_end))
            elif segments:
                ls, le = segments[-1]
                if ch_end - ls <= CLIP_MAX:
                    segments[-1] = (ls, ch_end)
    return segments


def process_clip(raw_path, out_path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(raw_path)],
        capture_output=True, text=True)
    w, h = map(int, r.stdout.strip().split(','))

    crop_w = min(int(h * 9 / 16), w)
    crop_h = h if crop_w < w else min(int(w * 16 / 9), h)
    x_off = (w - crop_w) // 2
    y_off = (h - crop_h) // 2

    vf = (
        f"crop={crop_w}:{crop_h}:{x_off}:{y_off},"
        f"scale=1080:1920,"
        f"drawtext=text='mxm':fontfile={FONT}:fontsize=72"
        f":fontcolor=white@0.7:x=w-tw-40:y=h-th-40,"
        f"drawtext=text='Wait for it\\.\\.\\.':fontfile={FONT}:fontsize=56"
        f":fontcolor=white:x=(w-tw)/2:y=h*0.45"
        f":box=1:boxcolor=black@0.5:boxborderw=10"
        f":enable='between(t,15,18)'"
    )
    subprocess.run([
        'ffmpeg', '-y', '-i', str(raw_path), '-vf', vf,
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
    return r2.json().get('id') if r2.status_code in (200, 201) else None


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


def main():
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print('=== The BEST Showboats — Shorts Pipeline ===\n')
    token = get_drive_token()

    print(f'Pass 1 — major transitions (threshold {THRESH_MAJOR})...')
    major_times, duration = detect_scenes(SRC, THRESH_MAJOR)
    print(f'  → {len(major_times)-2} major transitions | {duration:.0f}s ({duration/60:.1f} min)')

    print(f'Pass 2 — fine cuts (threshold {THRESH_FINE})...')
    fine_times, _ = detect_scenes(SRC, THRESH_FINE)
    print(f'  → {len(fine_times)-2} fine cuts detected\n')

    all_segments = build_segments(major_times, fine_times)
    total_all = len(all_segments)

    segments = all_segments[:PROCESS_LIMIT] if PROCESS_LIMIT else all_segments
    print(f'Total segments detected: {total_all}')
    print(f'Processing first {len(segments)} of {total_all}:\n')
    for i, (s, e) in enumerate(segments, 1):
        print(f'  Clip {i}: {s:.0f}s → {e:.0f}s ({e-s:.0f}s)')

    folder_id = get_or_create_folder(FOLDER_NAME, SHORTS_ROOT, token)
    print(f'\nDrive folder ready\n')

    for i, (start, end) in enumerate(segments, 1):
        raw_path = CLIPS_DIR / f'raw_{i:03d}.mp4'
        out_name = f'{SHORT_TITLES[i-1]}.mp4'
        out_path = PROCESSED_DIR / out_name

        print(f'[{i}/{len(segments)}] {out_name.replace(".mp4","").replace("_"," ")} ({end-start:.0f}s)')
        subprocess.run(['ffmpeg', '-y', '-ss', str(start), '-i', str(SRC),
            '-t', str(end - start), '-c', 'copy', str(raw_path)], capture_output=True)
        process_clip(raw_path, out_path)

        fid = save_to_drive(out_path, out_name, folder_id, token)
        print(f'  ✓ Saved to Drive: {out_name}' if fid else f'  ✗ Drive save failed')

    if not PROCESS_LIMIT:
        move_to_completed(DRIVE_FILE_ID, token)
        print(f'\n✓ Source moved to Completed')

    print(f'\n=== Done — {len(segments)} of {total_all} Shorts in Drive ===')
    if PROCESS_LIMIT:
        print(f'⚠️  Review first {PROCESS_LIMIT} clips, then set PROCESS_LIMIT = None to process the rest.')


if __name__ == '__main__':
    main()
