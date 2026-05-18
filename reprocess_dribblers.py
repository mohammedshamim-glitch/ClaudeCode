#!/usr/bin/env python3
"""
Reprocess Top 10 Dribblers with simplified pipeline:
- Delete existing Drive shorts folder
- Two-pass scene detection, no OCR, no overlays, no fade
- Name clips: Top-10-Dribblers_short_001.mp4, _002, etc.
"""

import json, re, subprocess, requests, shutil, random
from pathlib import Path

TOKEN_FILE   = '/home/user/ClaudeCode/token.json'
SHORTS_ROOT  = '10puXRPV_81umNFxxirV3zzF3x6XnvlML'
FOLDER_NAME  = 'Top 10 Dribblers 2025-26'
SRC          = Path('/home/user/ClaudeCode/mxm_shorts/downloads/Top-10-Dribblers.mp4')
CLIPS_DIR    = Path('/home/user/ClaudeCode/mxm_shorts/clips/dribblers_clean')
PROCESSED_DIR = Path('/home/user/ClaudeCode/mxm_shorts/processed')
FONT         = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

CLIP_MAX     = 55
CLIP_MIN     = 30
THRESH_MAJOR = 0.55
THRESH_FINE  = 0.25
def generate_titles(n):
    openers = [
        "When", "Watch", "See_How", "The_Moment", "Nobody_Expected",
        "Defenders_Couldnt_Stop", "Witness", "Remember_When",
    ]
    subjects = [
        "One_Player", "A_Single_Dribble", "Elite_Skills", "Perfect_Touch",
        "One_Move", "Close_Control", "Pure_Pace", "Raw_Talent",
        "Football_Magic", "The_Skill", "Insane_Footwork", "The_Dribble",
    ]
    connectors = [
        "Changed_The_Game", "Broke_The_Internet", "Left_Defenders_Behind",
        "Went_Viral", "Made_The_Crowd_Erupt", "Nobody_Saw_Coming",
        "Silenced_Everyone", "Was_Simply_Unstoppable", "Rewrote_The_Rules",
        "Took_Over_The_Pitch", "Had_No_Answer", "Made_History",
        "Broke_Ankles", "Was_On_Another_Level", "Cant_Be_Taught",
    ]
    standalones = [
        "Elite_Football_Skills_You_Wont_Forget",
        "Defenders_Had_No_Chance_Whatsoever",
        "Built_Different_Football_Masterclass",
        "Peak_Football_Right_Here",
        "Insane_Close_Control_At_Its_Best",
        "Football_Wizardry_Pure_And_Simple",
        "One_V_One_And_It_Wasnt_Even_Close",
        "Ankle_Breaking_Skills_2025",
        "You_Cant_Defend_This_Level_Of_Skill",
        "Speed_Skill_And_Pure_Brilliance",
        "The_Dribble_That_Froze_The_Defender",
        "How_Is_This_Even_Possible",
        "Leaving_Everyone_In_The_Dust",
        "Touch_Of_A_Genius_Football_Moment",
        "Football_At_Its_Absolute_Finest",
    ]
    generated = set()
    titles = []
    combos = [f"{o}_{s}_{c}" for o in openers for s in subjects for c in connectors]
    random.shuffle(combos)
    for c in combos:
        if c not in generated:
            generated.add(c)
            titles.append(c)
        if len(titles) >= n:
            return titles
    random.shuffle(standalones)
    for s in standalones:
        if s not in generated:
            generated.add(s)
            titles.append(s)
        if len(titles) >= n:
            return titles
    return titles


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


def build_segments(major_times, fine_times, duration):
    chapters = [(major_times[i], major_times[i+1]) for i in range(len(major_times)-1)]

    # Merge short chapters
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
            # Split using fine cuts
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


def cut_clip(src, start, end, out_path):
    subprocess.run(['ffmpeg', '-y', '-ss', str(start), '-i', str(src),
        '-t', str(end - start), '-c', 'copy', str(out_path)], capture_output=True)


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
        f":fontcolor=white@0.7:x=w-tw-40:y=h-th-40"
    )

    subprocess.run([
        'ffmpeg', '-y', '-i', str(raw_path),
        '-vf', vf,
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


def delete_drive_folder_contents(folder_id, token):
    """Delete all files inside a Drive folder, then delete the folder itself."""
    r = requests.get('https://www.googleapis.com/drive/v3/files',
        params={'q': f"'{folder_id}' in parents and trashed=false", 'fields': 'files(id,name)', 'pageSize': 100},
        headers={'Authorization': f'Bearer {token}'})
    files = r.json().get('files', [])
    for f in files:
        requests.delete(f"https://www.googleapis.com/drive/v3/files/{f['id']}",
            headers={'Authorization': f'Bearer {token}'})
        print(f"  Deleted: {f['name']}")
    requests.delete(f"https://www.googleapis.com/drive/v3/files/{folder_id}",
        headers={'Authorization': f'Bearer {token}'})
    print(f"  Deleted folder.")


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


def main():
    print('=== Reprocessing Top 10 Dribblers (clean pipeline) ===\n')
    token = get_drive_token()

    # 1. Find and delete existing Drive shorts folder
    print('Step 1: Removing existing Drive shorts...')
    r = requests.get('https://www.googleapis.com/drive/v3/files',
        params={'q': f"'{SHORTS_ROOT}' in parents and mimeType='application/vnd.google-apps.folder' and name='{FOLDER_NAME}' and trashed=false",
                'fields': 'files(id,name)'},
        headers={'Authorization': f'Bearer {token}'})
    folders = r.json().get('files', [])
    if folders:
        delete_drive_folder_contents(folders[0]['id'], token)
    else:
        print('  No existing folder found.')

    # 2. Clean local old processed files for this video
    print('\nStep 2: Cleaning local old processed files...')
    if CLIPS_DIR.exists():
        shutil.rmtree(CLIPS_DIR)
        print(f'  Cleared {CLIPS_DIR}')
    for title in TITLE_POOL:
        for f in PROCESSED_DIR.glob(f'{title}.mp4'):
            f.unlink()
            print(f'  Removed {f.name}')
    # Also remove old OCR-named files from previous run
    old_names = ['DRIBBLERS_', 'PASALIC_', 'Football_Skills_', 'KYLIAAT_', 'QATAR_',
                 'VINICIUS_', 'notordla_', 'WORLDS_', 'LUIS_']
    for prefix in old_names:
        for f in PROCESSED_DIR.glob(f'{prefix}*.mp4'):
            f.unlink()
            print(f'  Removed {f.name}')

    # 3. Two-pass scene detection
    print(f'\nStep 3: Scene detection on {SRC.name}...')
    print(f'  Pass 1 — major transitions (threshold {THRESH_MAJOR})...')
    major_times, duration = detect_scenes(SRC, THRESH_MAJOR)
    print(f'  → {len(major_times)-2} major transitions | {duration:.0f}s ({duration/60:.1f} min)')

    print(f'  Pass 2 — fine cuts (threshold {THRESH_FINE})...')
    fine_times, _ = detect_scenes(SRC, THRESH_FINE)
    print(f'  → {len(fine_times)-2} fine cuts detected')

    segments = build_segments(major_times, fine_times, duration)
    print(f'\n  → {len(segments)} Shorts to create')
    for i, (s, e) in enumerate(segments, 1):
        print(f'    Clip {i}: {s:.0f}s → {e:.0f}s ({e-s:.0f}s)')

    # 4. Create Drive folder
    folder_id = get_or_create_folder(FOLDER_NAME, SHORTS_ROOT, token)
    print(f'\nDrive folder ready')

    # 5. Cut, process, upload
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    titles = generate_titles(len(segments))

    for i, (start, end) in enumerate(segments, 1):
        raw_path = CLIPS_DIR / f'raw_{i:03d}.mp4'
        out_name = f'{titles[i-1]}.mp4'
        out_path = PROCESSED_DIR / out_name

        print(f'\n[{i}/{len(segments)}] {start:.0f}s–{end:.0f}s ({end-start:.0f}s)')
        cut_clip(SRC, start, end, raw_path)
        process_clip(raw_path, out_path)

        fid = save_to_drive(out_path, out_name, folder_id, token)
        if fid:
            print(f'  ✓ Saved to Drive: {out_name}')
        else:
            print(f'  ✗ Drive save failed for {out_name}')

        if i % 8 == 0:
            token = get_drive_token()

    print(f'\n=== Done — {len(segments)} Shorts in Drive ===')
    print('Awaiting confirmation before YouTube upload.')


if __name__ == '__main__':
    main()
