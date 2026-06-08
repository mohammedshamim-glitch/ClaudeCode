#!/usr/bin/env python3
"""
Build a ~10min compilation from Shorts clips and upload to YouTube.
Converts vertical (9:16) clips to 16:9 with blurred background.
Generates thumbnail with title text.
"""

import json, subprocess, requests, tempfile
from pathlib import Path

TOKEN_FILE   = '/home/user/ClaudeCode/token.json'
FONT         = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
WORK_DIR     = Path('/home/user/ClaudeCode/mxm_shorts/compilation')
PUBLISH_AT   = '2026-05-30T11:00:00Z'   # 30 May 12:00 BST

VIDEO_TITLE  = 'Best Football Skills & Goals 2025 🔥 Messi, Elite Dribblers & Incredible Showboats'
DESCRIPTION  = """\
The very best football skills, goals and showboating moments from 2025. Featuring Lionel Messi at his absolute best, elite dribblers destroying defenders, and the Premier League showboats that made crowds go wild.

⏱ Timestamps:
0:00 - Elite Dribblers
3:30 - Premier League Showboats
5:30 - Lionel Messi Goals

🔔 Subscribe for daily football clips!

#Football #Skills #Messi #Goals #PremierLeague #Dribblers #Highlights #FootballSkills #BestGoals2025 #mxmballers
"""
TAGS = [
    'Football', 'Skills', 'Messi', 'Goals', 'PremierLeague', 'Dribblers',
    'Highlights', 'FootballSkills', 'BestGoals2025', 'mxmballers',
    'Showboats', 'LionelMessi', 'FootballHighlights', 'BestFootball',
    'EliteDribblers', 'FootballMagic', 'TopGoals',
]

REMUSICED  = Path('/home/user/ClaudeCode/mxm_shorts/remusiced')
HOOK_DIR   = Path('/home/user/ClaudeCode/mxm_shorts/processed/dribblers_hook')
MESSI_DIR  = Path('/home/user/ClaudeCode/mxm_shorts/processed/messi')
MUSIC      = Path('/home/user/ClaudeCode/mxm_shorts/music/upbeat_background_2.mp3')

# Curated selection — 6 dribblers + 4 showboats + 6 messi ≈ 10 min
CLIPS = [
    HOOK_DIR   / 'Football_Wizardry_Dribbling_Edition.mp4',
    HOOK_DIR   / 'Defenders_Nightmare_Insane_Close_Control.mp4',
    HOOK_DIR   / 'When_Dribbling_Becomes_Pure_Art.mp4',
    HOOK_DIR   / 'Impossible_Touches_Only_The_Best_Can_Do.mp4',
    HOOK_DIR   / 'Next_Level_Dribbling_You_Wont_Believe.mp4',
    HOOK_DIR   / 'One_V_One_And_Its_Not_Even_Close.mp4',
    REMUSICED  / 'The_Showboat_That_Made_The_Crowd_Go_Crazy.mp4',
    REMUSICED  / 'When_Players_Forgot_They_Were_Playing_Football.mp4',
    REMUSICED  / 'The_Skill_Nobody_Asked_For_But_Everyone_Loved.mp4',
    REMUSICED  / 'Premier_League_Showboating_At_Its_Absolute_Peak.mp4',
    MESSI_DIR  / 'Messi_Makes_It_Look_Effortless.mp4',
    MESSI_DIR  / 'The_Goal_Only_Messi_Scores.mp4',
    MESSI_DIR  / 'Messi_Leaves_The_Keeper_No_Chance.mp4',
    MESSI_DIR  / 'Only_Messi_Can_Do_This.mp4',
    MESSI_DIR  / 'Messi_At_His_Absolute_Best.mp4',
    MESSI_DIR  / 'Messi_Does_It_Again.mp4',
]


def get_duration(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
        capture_output=True, text=True)
    return float(r.stdout.strip())


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


def to_16x9(src, out):
    """Convert vertical 9:16 clip to 16:9 with blurred background."""
    vf = (
        "[0:v]split[fg][bg];"
        "[bg]scale=1920:1080,boxblur=luma_radius=40:luma_power=3[blurred];"
        "[fg]scale=608:1080[fgs];"
        "[blurred][fgs]overlay=(W-w)/2:0[v]"
    )
    subprocess.run([
        'ffmpeg', '-y', '-i', str(src),
        '-filter_complex', vf, '-map', '[v]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-an', str(out)
    ], capture_output=True, check=True)


def make_thumbnail(clip_path, out_path, title):
    """Extract frame at 5s, apply 16:9 blurred background, add title text."""
    # Extract raw frame
    frame = out_path.parent / 'thumb_raw.mp4'
    vf = (
        "[0:v]split[fg][bg];"
        "[bg]scale=1920:1080,boxblur=luma_radius=40:luma_power=3[blurred];"
        "[fg]scale=608:1080[fgs];"
        "[blurred][fgs]overlay=(W-w)/2:0,"
        "scale=1280:720,"
        # Dark gradient overlay for text legibility
        "drawbox=x=0:y=540:w=1280:h=180:color=black@0.55:t=fill,"
        # Main title — split across two lines via two drawtext calls
        f"drawtext=text='Best Football Skills & Goals 2025':fontfile={FONT}"
        ":fontsize=54:fontcolor=white:x=(w-tw)/2:y=570:shadowcolor=black@0.8:shadowx=2:shadowy=2,"
        f"drawtext=text='Messi \\| Dribblers \\| Showboats':fontfile={FONT}"
        ":fontsize=34:fontcolor=white@0.9:x=(w-tw)/2:y=638:shadowcolor=black@0.8:shadowx=2:shadowy=2"
    )
    subprocess.run([
        'ffmpeg', '-y', '-ss', '5', '-i', str(clip_path),
        '-vf', vf, '-vframes', '1', str(out_path)
    ], capture_output=True, check=True)


def upload_video_with_thumbnail(video_path, thumb_path, token):
    size = video_path.stat().st_size
    r = requests.post(
        'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(size)},
        json={
            'snippet': {
                'title': VIDEO_TITLE,
                'description': DESCRIPTION,
                'tags': TAGS,
                'categoryId': '17',
                'defaultLanguage': 'en-GB',
                'defaultAudioLanguage': 'en-GB',
            },
            'status': {
                'privacyStatus': 'private',
                'publishAt': PUBLISH_AT,
                'selfDeclaredMadeForKids': False,
            },
        })
    r.raise_for_status()

    with open(video_path, 'rb') as f:
        r2 = requests.put(r.headers['Location'],
            headers={'Content-Type': 'video/mp4', 'Content-Length': str(size)}, data=f)
    if r2.status_code not in (200, 201):
        raise Exception(f'Upload failed: {r2.status_code} {r2.text[:200]}')

    video_id = r2.json()['id']

    # Upload thumbnail
    thumb_size = thumb_path.stat().st_size
    r3 = requests.post(
        f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}&uploadType=media',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'image/jpeg',
                 'Content-Length': str(thumb_size)},
        data=thumb_path.read_bytes())
    thumb_ok = r3.status_code in (200, 201)

    return video_id, thumb_ok


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out_16x9_dir = WORK_DIR / '16x9'
    out_16x9_dir.mkdir(exist_ok=True)

    print('=== Compilation Builder ===\n')

    # Step 1 — convert each clip to 16:9
    print('Step 1 — Converting clips to 16:9 with blurred background...')
    converted = []
    total_dur = 0.0
    for i, clip in enumerate(CLIPS, 1):
        out = out_16x9_dir / f'{i:02d}_{clip.stem}.mp4'
        if not out.exists():
            print(f'  [{i:02d}/{len(CLIPS)}] {clip.stem[:45]}...')
            to_16x9(clip, out)
        else:
            print(f'  [{i:02d}/{len(CLIPS)}] ↩ {clip.stem[:45]}')
        dur = get_duration(out)
        total_dur += dur
        converted.append(out)

    print(f'\n  Total duration: {total_dur:.0f}s ({total_dur/60:.1f} min)\n')

    # Step 2 — build concat list
    concat_file = WORK_DIR / 'concat.txt'
    with open(concat_file, 'w') as f:
        for p in converted:
            f.write(f"file '{p}'\n")

    # Step 3 — concatenate + add music
    print('Step 2 — Concatenating and adding music...')
    silent_concat = WORK_DIR / 'concat_silent.mp4'
    final_video   = WORK_DIR / 'compilation_final.mp4'

    if not silent_concat.exists():
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', str(concat_file), '-c', 'copy', str(silent_concat)
        ], capture_output=True, check=True)

    if not final_video.exists():
        subprocess.run([
            'ffmpeg', '-y',
            '-i', str(silent_concat),
            '-stream_loop', '-1', '-i', str(MUSIC),
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
            '-shortest', '-movflags', '+faststart',
            str(final_video)
        ], capture_output=True, check=True)

    final_dur = get_duration(final_video)
    print(f'  ✓ Final video: {final_dur:.0f}s ({final_dur/60:.1f} min), {final_video.stat().st_size//1024//1024}MB\n')

    # Step 4 — thumbnail
    print('Step 3 — Generating thumbnail...')
    thumb_path = WORK_DIR / 'thumbnail.jpg'
    if not thumb_path.exists():
        # Use a Messi clip for the thumbnail — good visual
        make_thumbnail(MESSI_DIR / 'Messi_At_His_Absolute_Best.mp4', thumb_path, VIDEO_TITLE)
    print(f'  ✓ Thumbnail: {thumb_path.stat().st_size//1024}KB\n')

    # Step 5 — upload
    print('Step 4 — Uploading to YouTube...')
    token = get_youtube_token()
    video_id, thumb_ok = upload_video_with_thumbnail(final_video, thumb_path, token)
    print(f'  ✓ Video uploaded: https://www.youtube.com/watch?v={video_id}')
    print(f'  {"✓ Thumbnail set" if thumb_ok else "⚠ Thumbnail upload failed — set manually in Studio"}')
    print(f'  ✓ Scheduled: 30 May 12:00 BST')
    print(f'\n=== Done ===')


if __name__ == '__main__':
    main()
