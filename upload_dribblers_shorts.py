#!/usr/bin/env python3
"""
Upload Top 10 Dribblers Shorts to mxm ballers YouTube channel.
- Trims first 10s from clip 1 (Ankle_Breaking)
- Checks existing scheduled videos to avoid double-booking
- Schedules 1 per day at 18:00 BST (17:00 UTC)
"""

import json, re, subprocess, requests, os, tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone

TOKEN_FILE    = '/home/user/ClaudeCode/token.json'
SHORTS_ROOT   = '10puXRPV_81umNFxxirV3zzF3x6XnvlML'
FOLDER_NAME   = 'Top 10 Dribblers 2025-26'
LOCAL_DIR     = Path('/home/user/ClaudeCode/mxm_shorts/processed')
WORK_DIR      = Path('/home/user/ClaudeCode/mxm_shorts/trimmed')

# Drive filenames in upload order (matches local short_001 → short_012)
CLIPS = [
    ("Ankle_Breaking_Dribbles_Nobody_Saw_Coming",       "🤯", True),   # trim first 10s
    ("When_One_Player_Beats_The_Whole_Defence",          "😤", False),
    ("Elite_Dribbling_Skills_At_Their_Finest",           "🔥", False),
    ("The_Dribble_That_Left_Defenders_Frozen",           "⚡", False),
    ("Speed_And_Skill_Unstoppable_Football_Moments",     "💨", False),
    ("Football_Wizardry_Dribbling_Edition",              "🪄", False),
    ("Defenders_Nightmare_Insane_Close_Control",         "💀", False),
    ("When_Dribbling_Becomes_Pure_Art",                  "🎨", False),
    ("Impossible_Touches_Only_The_Best_Can_Do",          "🐐", False),
    ("Next_Level_Dribbling_You_Wont_Believe",            "👀", False),
    ("One_V_One_And_Its_Not_Even_Close",                 "😭", False),
    ("Best_Dribble_Of_The_Season_Right_Here",            "🏆", False),
]


def format_title(stem, emoji):
    return f"{stem.replace('_', ' ')} {emoji} #Shorts #Football"


def format_description(title):
    return (
        f"{title}\n\n"
        f"Follow @mxmballers for daily football content 🙌\n\n"
        f"#Shorts #Football #Skills #Dribbling #Soccer #mxmballers #FootballShorts"
    )


# ── Auth ──────────────────────────────────────────────────────────────────────

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


# ── Drive ─────────────────────────────────────────────────────────────────────

def get_dribblers_folder(drive_token):
    r = requests.get('https://www.googleapis.com/drive/v3/files',
        params={'q': f"'{SHORTS_ROOT}' in parents and name='{FOLDER_NAME}' and trashed=false",
                'fields': 'files(id)'},
        headers={'Authorization': f'Bearer {drive_token}'})
    return r.json()['files'][0]['id']


def list_drive_clips(folder_id, drive_token):
    r = requests.get('https://www.googleapis.com/drive/v3/files',
        params={'q': f"'{folder_id}' in parents and trashed=false",
                'fields': 'files(id,name)', 'orderBy': 'name', 'pageSize': 50},
        headers={'Authorization': f'Bearer {drive_token}'})
    return {f['name'].replace('.mp4', ''): f['id'] for f in r.json()['files']}


def download_from_drive(file_id, dest, drive_token):
    if dest.exists():
        return
    r = requests.get(f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media',
        headers={'Authorization': f'Bearer {drive_token}'}, stream=True)
    r.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(1024 * 1024):
            f.write(chunk)


def update_drive_file(file_id, path, drive_token):
    """Replace file content on Drive (keeps same ID and name)."""
    size = path.stat().st_size
    r = requests.patch(
        f'https://www.googleapis.com/upload/drive/v3/files/{file_id}?uploadType=resumable',
        headers={'Authorization': f'Bearer {drive_token}', 'Content-Type': 'application/json',
                 'X-Upload-Content-Type': 'video/mp4'},
        json={})
    r.raise_for_status()
    with open(path, 'rb') as f:
        r2 = requests.put(r.headers['Location'],
            headers={'Content-Type': 'video/mp4', 'Content-Length': str(size)}, data=f)
    return r2.status_code in (200, 201)


# ── YouTube ───────────────────────────────────────────────────────────────────

def get_scheduled_dates(yt_token):
    """Return set of dates (YYYY-MM-DD) that already have a scheduled upload."""
    # Get uploads playlist
    r = requests.get('https://www.googleapis.com/youtube/v3/channels',
        params={'part': 'contentDetails', 'mine': 'true'},
        headers={'Authorization': f'Bearer {yt_token}'})
    playlist_id = r.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # Get recent video IDs
    r2 = requests.get('https://www.googleapis.com/youtube/v3/playlistItems',
        params={'part': 'contentDetails', 'playlistId': playlist_id, 'maxResults': 50},
        headers={'Authorization': f'Bearer {yt_token}'})
    ids = [i['contentDetails']['videoId'] for i in r2.json().get('items', [])]
    if not ids:
        return set()

    # Check statuses in batches of 50
    occupied = set()
    for i in range(0, len(ids), 50):
        batch = ','.join(ids[i:i+50])
        r3 = requests.get('https://www.googleapis.com/youtube/v3/videos',
            params={'part': 'status', 'id': batch},
            headers={'Authorization': f'Bearer {yt_token}'})
        for item in r3.json().get('items', []):
            publish_at = item['status'].get('publishAt')
            if publish_at:
                occupied.add(publish_at[:10])  # YYYY-MM-DD
    return occupied


def next_schedule_date(occupied, from_date):
    """Find the next date not in occupied, starting from from_date."""
    d = from_date
    while d.strftime('%Y-%m-%d') in occupied:
        d += timedelta(days=1)
    return d


def upload_to_youtube(video_path, title, description, publish_at_utc, yt_token):
    """Upload Short with scheduled publish time. publish_at_utc is a datetime in UTC."""
    publish_str = publish_at_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    metadata = {
        'snippet': {
            'title': title[:100],
            'description': description,
            'tags': ['football', 'soccer', 'skills', 'dribbling', 'shorts',
                     'football shorts', 'mxm ballers', 'mxmballers'],
            'categoryId': '17',
            'defaultLanguage': 'en-GB',
            'defaultAudioLanguage': 'en-GB',
        },
        'status': {
            'privacyStatus': 'private',
            'publishAt': publish_str,
            'selfDeclaredMadeForKids': False,
        },
    }
    r = requests.post(
        'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
        headers={'Authorization': f'Bearer {yt_token}', 'Content-Type': 'application/json',
                 'X-Upload-Content-Type': 'video/mp4'},
        json=metadata)
    r.raise_for_status()
    size = video_path.stat().st_size
    with open(video_path, 'rb') as f:
        r2 = requests.put(r.headers['Location'],
            headers={'Content-Type': 'video/mp4', 'Content-Length': str(size)}, data=f)
    if r2.status_code in (200, 201):
        return r2.json().get('id')
    print(f'  ✗ Upload failed: {r2.status_code} {r2.text[:200]}')
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    print('=== mxm ballers — Upload Dribblers Shorts ===\n')
    drive_token = get_drive_token()
    yt_token    = get_youtube_token()

    # Get Drive file IDs
    folder_id  = get_dribblers_folder(drive_token)
    drive_map  = list_drive_clips(folder_id, drive_token)
    print(f'Found {len(drive_map)} clips on Drive\n')

    # Step 1: trim first 10s from Ankle_Breaking
    print('Step 1: Trimming Ankle_Breaking_Dribbles_Nobody_Saw_Coming...')
    ankle_stem = 'Ankle_Breaking_Dribbles_Nobody_Saw_Coming'
    local_001  = LOCAL_DIR / 'Top-10-Dribblers_short_001.mp4'
    trimmed    = WORK_DIR / f'{ankle_stem}_trimmed.mp4'

    if not trimmed.exists():
        subprocess.run([
            'ffmpeg', '-y', '-ss', '10', '-i', str(local_001),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart',
            str(trimmed)
        ], capture_output=True)
        print(f'  ✓ Trimmed locally')

    # Update Drive with trimmed version
    if ankle_stem in drive_map:
        ok = update_drive_file(drive_map[ankle_stem], trimmed, drive_token)
        print(f'  ✓ Drive updated' if ok else '  ✗ Drive update failed')
    print()

    # Step 2: check existing scheduled dates
    print('Step 2: Checking existing scheduled uploads...')
    occupied = get_scheduled_dates(yt_token)
    if occupied:
        print(f'  Already scheduled on: {", ".join(sorted(occupied))}')
    else:
        print('  No scheduled uploads found')
    print()

    # Step 3: upload all 12, 1 per day at 18:00 BST (17:00 UTC)
    print('Step 3: Uploading 12 Shorts...\n')

    # Start from tomorrow
    utc = timezone.utc
    next_day = datetime.now(utc).replace(hour=17, minute=0, second=0, microsecond=0)
    next_day += timedelta(days=1)

    local_files = {
        f'Top-10-Dribblers_short_{i:03d}': LOCAL_DIR / f'Top-10-Dribblers_short_{i:03d}.mp4'
        for i in range(1, 13)
    }

    for idx, (stem, emoji, trim) in enumerate(CLIPS, 1):
        local_key = f'Top-10-Dribblers_short_{idx:03d}'
        video_path = trimmed if trim else local_files[local_key]

        title       = format_title(stem, emoji)
        description = format_description(title)

        # Find next free slot
        sched = next_schedule_date(occupied, next_day)
        occupied.add(sched.strftime('%Y-%m-%d'))
        next_day = sched + timedelta(days=1)

        sched_utc = sched.replace(hour=17, minute=0, second=0, microsecond=0)
        sched_bst = sched.strftime('%d %b %Y')

        print(f'[{idx}/12] {title}')
        print(f'  Scheduled: {sched_bst} at 18:00 BST')

        vid_id = upload_to_youtube(video_path, title, description, sched_utc, yt_token)
        if vid_id:
            print(f'  ✓ https://www.youtube.com/shorts/{vid_id}')
        else:
            print(f'  ✗ Failed')

        # Refresh token every 4 uploads
        if idx % 4 == 0:
            yt_token = get_youtube_token()
        print()

    print('=== Done — 12 Shorts scheduled ===')
    print('⚠️  All set to private with scheduled publish times. Review in YouTube Studio.')


if __name__ == '__main__':
    main()
