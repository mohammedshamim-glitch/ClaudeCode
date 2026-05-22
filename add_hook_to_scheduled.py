#!/usr/bin/env python3
"""
Re-process 7 scheduled Dribblers clips with the mid-clip text hook,
delete the old YouTube upload, and re-upload with the same schedule.
"""

import json, subprocess, requests, time
from pathlib import Path
from datetime import datetime, timezone

TOKEN_FILE   = '/home/user/ClaudeCode/token.json'
FONT         = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
RAW_DIR      = Path('/home/user/ClaudeCode/mxm_shorts/clips/dribblers_clean')
HOOK_DIR     = Path('/home/user/ClaudeCode/mxm_shorts/processed/dribblers_hook')
MUSIC_FILE   = Path('/home/user/ClaudeCode/mxm_shorts/music/upbeat_background_1.mp3')

# 7 clips being re-processed: raw clip → (video_id, publish_at_utc, title_stem, emoji)
TARGETS = [
    ('raw_006.mp4', 'YPV41Te-zj4', '2026-05-25T16:00:00Z', 'Football_Wizardry_Dribbling_Edition', '🎩'),
    ('raw_007.mp4', 'k5KOVosLePk', '2026-05-26T16:00:00Z', 'Defenders_Nightmare_Insane_Close_Control', '😤'),
    ('raw_008.mp4', '4Oa8rcdJBps', '2026-05-27T16:00:00Z', 'When_Dribbling_Becomes_Pure_Art', '🎨'),
    ('raw_009.mp4', 'qZAioaT_7eY', '2026-05-28T16:00:00Z', 'Impossible_Touches_Only_The_Best_Can_Do', '🤯'),
    ('raw_010.mp4', 'ZNaqrxHe70Q', '2026-05-29T16:00:00Z', 'Next_Level_Dribbling_You_Wont_Believe', '🚀'),
    ('raw_011.mp4', '81o4UdfXC8c', '2026-05-30T16:00:00Z', 'One_V_One_And_Its_Not_Even_Close', '💥'),
    ('raw_012.mp4', 'Ni4DqkFAY6E', '2026-05-31T16:00:00Z', 'Best_Dribble_Of_The_Season_Right_Here', '🏆'),
]


def get_youtube_token():
    with open(TOKEN_FILE) as f:
        t = json.load(f)
    r = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id':     t['client_id'],
        'client_secret': t['client_secret'],
        'refresh_token': t['youtube_refresh_token'],
        'grant_type':    'refresh_token',
    })
    r.raise_for_status()
    token = r.json()['access_token']
    t['youtube_access_token'] = token
    with open(TOKEN_FILE, 'w') as f:
        json.dump(t, f, indent=2)
    return token


def process_clip_with_hook(raw_path, out_path):
    """Crop → 9:16, watermark, mid-clip hook, replace audio with royalty-free music."""
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(raw_path)],
        capture_output=True, text=True)
    w, h = map(int, r.stdout.strip().split(','))

    crop_w = min(int(h * 9 / 16), w)
    crop_h = h if crop_w < w else min(int(w * 16 / 9), h)
    x_off  = (w - crop_w) // 2
    y_off  = (h - crop_h) // 2

    vf = (
        f"crop={crop_w}:{crop_h}:{x_off}:{y_off},"
        f"scale=1080:1920,"
        f"drawtext=text='mxm':fontfile={FONT}:fontsize=72"
        f":fontcolor=white@0.7:x=w-tw-40:y=h-th-40,"
        f"drawtext=text='Wait for it\\.\\.\\. 👀':fontfile={FONT}:fontsize=56"
        f":fontcolor=white:x=(w-tw)/2:y=h*0.45"
        f":box=1:boxcolor=black@0.5:boxborderw=10"
        f":enable='between(t,15,18)'"
    )

    subprocess.run([
        'ffmpeg', '-y',
        '-i', str(raw_path),
        '-stream_loop', '-1', '-i', str(MUSIC_FILE),
        '-vf', vf,
        '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest', '-movflags', '+faststart',
        str(out_path)
    ], capture_output=True, check=True)


def delete_video(video_id, token):
    r = requests.delete(
        f'https://www.googleapis.com/youtube/v3/videos',
        params={'id': video_id},
        headers={'Authorization': f'Bearer {token}'},
    )
    r.raise_for_status()


def upload_video(path, title_stem, emoji, publish_at, token):
    """Resumable upload then schedule."""
    title = f"{title_stem.replace('_', ' ')} {emoji} #Shorts #Football"
    description = (
        "🔥 Football skills you won't believe!\n\n"
        "#Shorts #Football #Skills #PremierLeague #Dribbling #mxmballers"
    )
    tags = ['Shorts', 'Football', 'Skills', 'Dribbling', 'PremierLeague', 'mxmballers',
            'FootballSkills', 'Highlights']

    size = path.stat().st_size
    r = requests.post(
        'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable'
        '&part=snippet,status',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-Upload-Content-Type': 'video/mp4',
            'X-Upload-Content-Length': str(size),
        },
        json={
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '17',
                'defaultLanguage': 'en-GB',
                'defaultAudioLanguage': 'en-GB',
            },
            'status': {
                'privacyStatus': 'private',
                'publishAt': publish_at,
                'selfDeclaredMadeForKids': False,
            },
        },
    )
    r.raise_for_status()
    upload_url = r.headers['Location']

    with open(path, 'rb') as f:
        r2 = requests.put(
            upload_url,
            headers={'Content-Type': 'video/mp4', 'Content-Length': str(size)},
            data=f,
        )
    if r2.status_code not in (200, 201):
        raise Exception(f'Upload failed: {r2.status_code} {r2.text[:200]}')

    video_id = r2.json()['id']
    # Parse BST display time
    dt = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
    bst_hour = (dt.hour + 1) % 24  # UTC+1 for BST
    return video_id, f"{dt.day:02d} {dt.strftime('%b')} {bst_hour:02d}:00 BST"


def main():
    HOOK_DIR.mkdir(parents=True, exist_ok=True)

    print('=== Adding mid-clip hook to 7 scheduled Dribblers ===\n')
    token = get_youtube_token()

    for raw_name, old_vid_id, publish_at, stem, emoji in TARGETS:
        raw_path = RAW_DIR / raw_name
        out_path = HOOK_DIR / f'{stem}.mp4'
        title    = f"{stem.replace('_', ' ')} {emoji} #Shorts #Football"

        print(f'Processing {stem.replace("_", " ")}...')

        # Step 1 — re-process with hook
        if not out_path.exists():
            process_clip_with_hook(raw_path, out_path)
            print(f'  ✓ Encoded with hook')
        else:
            print(f'  ↩ Already encoded')

        # Step 2 — delete old YouTube video
        try:
            delete_video(old_vid_id, token)
            print(f'  ✓ Deleted old: {old_vid_id}')
        except Exception as e:
            print(f'  ⚠ Delete failed ({old_vid_id}): {e}')

        # Step 3 — re-upload with same schedule
        try:
            new_id, sched_str = upload_video(out_path, stem, emoji, publish_at, token)
            print(f'  ✓ {sched_str} — https://www.youtube.com/shorts/{new_id}')
        except Exception as e:
            print(f'  ✗ Upload failed: {e}')
            continue

        time.sleep(2)

    print('\n=== Done ===')


if __name__ == '__main__':
    main()
