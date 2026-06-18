#!/usr/bin/env python3
"""Digital Fusion YouTube Pipeline — The Flaw in the Foundation"""
import json, re, subprocess, sys, time
from datetime import datetime
from pathlib import Path
import requests

# ── Credentials ───────────────────────────────────────────────────────────────
BASE = Path('/home/user/ClaudeCode')
with open(BASE / 'token.json') as f:
    T = json.load(f)

GEMINI_KEY    = T['gemini_api_key']
DF_REFRESH    = T['digital_fusion_refresh_token']
CLIENT_ID     = T['client_id']
CLIENT_SECRET = T['client_secret']

DRIVE_VIDEO_ID   = '11FO6qgnJ_50q5B3s84z1PwxPtQoG2UDG'
PROCESSED_FOLDER = '1q80MPi_hAfcCLeKsYCBOB-_vrBJCV26z'

TMP = Path('/tmp/df_flaw')
TMP.mkdir(exist_ok=True)
ORIG  = TMP / 'original.mp4'
PROC  = TMP / 'processed.mp4'
WAV   = TMP / 'audio.wav'
FRAME = TMP / 'frame.jpg'
THUMB = TMP / 'thumbnail.jpg'
TXTF  = TMP / 'transcript.txt'
SEOF  = TMP / 'seo_description.txt'

PUBLISH_AT = '2026-07-02T17:00:00.000Z'  # Thu 2 Jul 2026 18:00 BST

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_token(refresh):
    r = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
        'refresh_token': refresh, 'grant_type': 'refresh_token',
    }, timeout=30)
    r.raise_for_status()
    return r.json()['access_token']

def auth(tok): return {'Authorization': f'Bearer {tok}'}

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, **kw)
    if r.returncode != 0:
        print(r.stderr.decode()[-500:])
        sys.exit(1)
    return r

def upload_to_drive(path, name, mime, folder_id, tok):
    data = Path(path).read_bytes()
    init = requests.post(
        'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
        headers={**auth(tok), 'Content-Type': 'application/json',
                 'X-Upload-Content-Type': mime,
                 'X-Upload-Content-Length': str(len(data))},
        json={'name': name, 'parents': [folder_id]}, timeout=30
    )
    if not init.ok:
        print(f'  Drive init failed {init.status_code}: {init.text[:200]}')
        return None
    up = requests.put(init.headers['Location'], data=data,
                      headers={'Content-Type': mime}, timeout=600)
    if up.status_code not in (200, 201):
        print(f'  Drive upload failed {up.status_code}: {up.text[:200]}')
        return None
    return up.json()['id']

# ── Step 1: Download ──────────────────────────────────────────────────────────
print('[1/8] Downloading original video from Drive...')
tok = get_token(DF_REFRESH)
r = requests.get(
    f'https://www.googleapis.com/drive/v3/files/{DRIVE_VIDEO_ID}?alt=media',
    headers=auth(tok), stream=True, timeout=300
)
r.raise_for_status()
with open(ORIG, 'wb') as f:
    for chunk in r.iter_content(8192): f.write(chunk)
print(f'  ✓ {ORIG.stat().st_size // 1024 // 1024} MB')

# ── Step 2: Logo overlay (bottom-right 1280×720) ──────────────────────────────
print('[2/8] Adding Digital Fusion logo overlay (bottom-right)...')
run(['ffmpeg', '-y', '-i', str(ORIG),
     '-vf', (
         "drawbox=x=1040:y=662:w=230:h=48:color=black@0.85:t=fill,"
         "drawtext=text='Digital Fusion':fontsize=22:fontcolor=white:x=1052:y=673"
     ),
     '-c:a', 'copy', str(PROC)])
print(f'  ✓ {PROC.stat().st_size // 1024 // 1024} MB')

# ── Step 3: Extract audio WAV ─────────────────────────────────────────────────
print('[3/8] Extracting audio...')
run(['ffmpeg', '-y', '-i', str(PROC),
     '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', str(WAV)])
print(f'  ✓ {WAV.stat().st_size // 1024 // 1024} MB')

# ── Step 4: Transcribe via Gemini Files API ───────────────────────────────────
print('[4/8] Uploading audio to Gemini Files API...')
wav_bytes = WAV.read_bytes()
wav_size  = len(wav_bytes)

init = requests.post(
    f'https://generativelanguage.googleapis.com/upload/v1beta/files?uploadType=resumable&key={GEMINI_KEY}',
    headers={
        'X-Goog-Upload-Protocol': 'resumable',
        'X-Goog-Upload-Command': 'start',
        'X-Goog-Upload-Header-Content-Length': str(wav_size),
        'X-Goog-Upload-Header-Content-Type': 'audio/wav',
        'Content-Type': 'application/json',
    },
    json={'file': {'display_name': 'flaw_audio'}}, timeout=30
)
init.raise_for_status()
upload_url = init.headers['X-Goog-Upload-URL']

up = requests.post(upload_url, headers={
    'Content-Length': str(wav_size),
    'X-Goog-Upload-Offset': '0',
    'X-Goog-Upload-Command': 'upload, finalize',
}, data=wav_bytes, timeout=300)
up.raise_for_status()
file_info = up.json()['file']
file_uri  = file_info['uri']
file_name = file_info['name']
print(f'  ✓ Uploaded: {file_uri}')

print('  Waiting for ACTIVE state...')
for _ in range(30):
    st = requests.get(
        f'https://generativelanguage.googleapis.com/v1beta/{file_name}?key={GEMINI_KEY}',
        timeout=15
    ).json()
    if st.get('state') == 'ACTIVE':
        break
    time.sleep(3)

print('  Transcribing...')
tr = requests.post(
    f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}',
    json={'contents': [{'parts': [
        {'file_data': {'mime_type': 'audio/wav', 'file_uri': file_uri}},
        {'text': 'Transcribe this audio verbatim. Return only the transcript text, no timestamps or labels.'}
    ]}]},
    timeout=180
)
tr.raise_for_status()
transcript = tr.json()['candidates'][0]['content']['parts'][0]['text']
TXTF.write_text(transcript, encoding='utf-8')
print(f'  ✓ {len(transcript)} chars')

# ── Step 5: Generate SEO ──────────────────────────────────────────────────────
print('[5/8] Generating SEO metadata + LinkedIn draft...')
SEO_PROMPT = f"""You are a YouTube SEO expert for Digital Fusion, a UK finance and technology channel.

Using the transcript below, generate the following. Use EXACTLY these headers:

TITLE: Compelling YouTube title (max 60 chars, no emojis, no quotes)

DESCRIPTION:
Detailed, meaty description (minimum 400 words). Structure:
- Hook: 2-3 punchy sentences with specific stats/names from the video
- 4-5 body paragraphs packed with facts, figures, company names from the transcript
- "What you'll discover in this video:" + 6-8 bullet points (use -)
- "Don't forget to subscribe for more insights like this!"
- Chapters: 00:00 Intro, then 5-7 more chapters (estimate timestamps from content flow)
Do NOT use ** markdown in the description.

TAGS: 12 comma-separated tags (no # symbol, no quotes)

THUMBNAIL_LINE1: 3-5 words, white top line for thumbnail

THUMBNAIL_LINE2: 3-5 words, red punchline for thumbnail bottom

LINKEDIN_DRAFT:
UK-friendly long-form LinkedIn post. Include:
- Strong single-sentence hook
- 3-4 short paragraphs with key stats and named examples (£ not $, UK context)
- Emojis to break up text (🔑 💡 📉 ⚠️ etc.)
- Closing question call-to-action
- Video URL placeholder [VIDEO_URL] and 4-5 hashtags
Medium length, punchy. No excessive bullet lists.

TRANSCRIPT:
{transcript[:9000]}"""

seo_r = requests.post(
    f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}',
    json={'contents': [{'parts': [{'text': SEO_PROMPT}]}],
          'generationConfig': {'temperature': 0.7}},
    timeout=120
)
seo_r.raise_for_status()
seo_raw = seo_r.json()['candidates'][0]['content']['parts'][0]['text']
SEOF.write_text(seo_raw, encoding='utf-8')
print(f'  ✓ {len(seo_raw)} chars')

def get_field(text, key):
    m = re.search(rf'^{key}:\s*(.+?)(?=\n[A-Z_]{{3,}}:|\Z)', text, re.M | re.S)
    return m.group(1).strip() if m else ''

yt_title   = get_field(seo_raw, 'TITLE')
desc_raw   = get_field(seo_raw, 'DESCRIPTION')
tags_raw   = get_field(seo_raw, 'TAGS')
thumb1     = get_field(seo_raw, 'THUMBNAIL_LINE1')
thumb2     = get_field(seo_raw, 'THUMBNAIL_LINE2')
linkedin   = get_field(seo_raw, 'LINKEDIN_DRAFT')

desc = re.sub(r'\*\*(.+?)\*\*', r'\1', desc_raw)
desc = re.sub(r'^\s*\*\s+', '- ', desc, flags=re.M)
if len(desc) > 4900: desc = desc[:4900]

tags_list = [t.strip().strip('"').strip("'") for t in tags_raw.split(',') if t.strip()]

print(f'  Title:  {yt_title}')
print(f'  Thumb:  "{thumb1}" / "{thumb2}"')
print(f'  Tags:   {len(tags_list)}')

# ── Step 6: Build thumbnail ────────────────────────────────────────────────────
print('[6/8] Building thumbnail from video frame...')
dur_out = subprocess.run(
    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
     '-of', 'default=noprint_wrappers=1:nokey=1', str(PROC)],
    capture_output=True, text=True
)
duration = float(dur_out.stdout.strip())
run(['ffmpeg', '-y', '-ss', str(duration * 0.30), '-i', str(PROC),
     '-vframes', '1', '-q:v', '2', str(FRAME)])

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

img = Image.open(FRAME).convert('RGB').resize((1280, 720))
img = ImageEnhance.Brightness(img).enhance(0.60)
draw = ImageDraw.Draw(img)

# Left red accent bar
draw.rectangle([0, 0, 8, 720], fill='#DC1E1E')
# Brand box
draw.rectangle([18, 16, 270, 58], fill='black')

def load_font(size, bold=True):
    for p in [
        f'/usr/share/fonts/truetype/dejavu/DejaVuSans-{"Bold" if bold else ""}.ttf',
        f'/usr/share/fonts/truetype/liberation/LiberationSans-{"Bold" if bold else "Regular"}.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]:
        try: return ImageFont.truetype(p, size)
        except: pass
    return ImageFont.load_default()

def draw_wrapped(draw, text, font, x, y, fill, max_w=1190):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = ' '.join(cur + [w])
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] > max_w and cur:
            lines.append(' '.join(cur)); cur = [w]
        else:
            cur.append(w)
    if cur: lines.append(' '.join(cur))
    for line in lines:
        draw.text((x+3, y+3), line, font=font, fill='black')
        draw.text((x, y), line, font=font, fill=fill)
        bb = draw.textbbox((x, y), line, font=font)
        y += (bb[3] - bb[1]) + 14
    return y

draw.text((28, 25), 'Digital Fusion', font=load_font(22), fill='white')
y = draw_wrapped(draw, thumb1 or yt_title, load_font(100), 60, 160, 'white')
draw_wrapped(draw, thumb2 or '', load_font(100), 60, y + 20, '#DC1E1E')

img.save(str(THUMB), 'JPEG', quality=95)
print(f'  ✓ thumbnail.jpg')

# ── Step 7: Upload ALL assets to Drive first ───────────────────────────────────
print('[7/8] Creating Drive episode folder and uploading assets...')
tok = get_token(DF_REFRESH)
folder_name = yt_title[:80] if yt_title else 'The Flaw in the Foundation'
cr = requests.post(
    'https://www.googleapis.com/drive/v3/files',
    headers={**auth(tok), 'Content-Type': 'application/json'},
    json={'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder',
          'parents': [PROCESSED_FOLDER]},
    timeout=30
)
cr.raise_for_status()
EP_FOLDER = cr.json()['id']
print(f'  ✓ Episode folder: {EP_FOLDER}')

THUMB_DRIVE_ID = None
assets = [
    (ORIG,  'original.mp4',        'video/mp4'),
    (PROC,  'processed.mp4',       'video/mp4'),
    (THUMB, 'thumbnail.jpg',       'image/jpeg'),
    (TXTF,  'transcript.txt',      'text/plain'),
    (SEOF,  'seo_description.txt', 'text/plain'),
]
for path, name, mime in assets:
    tok = get_token(DF_REFRESH)
    fid = upload_to_drive(path, name, mime, EP_FOLDER, tok)
    print(f'  ✓ {name}: {fid}')
    if name == 'thumbnail.jpg':
        THUMB_DRIVE_ID = fid

# Make thumbnail public (for LinkedIn)
tok = get_token(DF_REFRESH)
requests.post(
    f'https://www.googleapis.com/drive/v3/files/{THUMB_DRIVE_ID}/permissions',
    headers={**auth(tok), 'Content-Type': 'application/json'},
    json={'role': 'reader', 'type': 'anyone'}, timeout=15
)
thumb_url = f'https://drive.google.com/uc?export=download&id={THUMB_DRIVE_ID}'
print(f'  ✓ Thumbnail public: {thumb_url}')

# ── Step 8: Upload to YouTube ─────────────────────────────────────────────────
print('[8/8] Uploading to YouTube (scheduled Thu 2 Jul 2026 18:00 BST)...')
tok = get_token(DF_REFRESH)

meta = {
    'snippet': {
        'title': yt_title,
        'description': desc,
        'tags': tags_list,
        'categoryId': '27',
        'defaultLanguage': 'en-GB',
        'defaultAudioLanguage': 'en-GB',
    },
    'status': {
        'privacyStatus': 'private',
        'publishAt': PUBLISH_AT,
        'selfDeclaredMadeForKids': False,
    }
}

video_bytes = PROC.read_bytes()
init = requests.post(
    'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
    headers={**auth(tok), 'Content-Type': 'application/json',
             'X-Upload-Content-Type': 'video/mp4',
             'X-Upload-Content-Length': str(len(video_bytes))},
    json=meta, timeout=30
)
if not init.ok:
    print(f'  ✗ YouTube init failed: {init.status_code} {init.text[:400]}')
    sys.exit(1)
yt_url = init.headers['Location']

up = requests.put(yt_url, data=video_bytes,
                  headers={'Content-Type': 'video/mp4'}, timeout=600)
if up.status_code not in (200, 201):
    print(f'  ✗ YouTube upload failed: {up.status_code} {up.text[:400]}')
    sys.exit(1)

yt_id = up.json()['id']
print(f'  ✓ YouTube ID: {yt_id}')

# Upload LinkedIn draft as Google Doc (preserves emojis, easy to copy-paste)
li_text = linkedin.replace('[VIDEO_URL]', f'https://www.youtube.com/watch?v={yt_id}')
li_data = li_text.encode('utf-8')
tok = get_token(DF_REFRESH)
init = requests.post(
    'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&convert=true',
    headers={**auth(tok), 'Content-Type': 'application/json',
             'X-Upload-Content-Type': 'text/plain',
             'X-Upload-Content-Length': str(len(li_data))},
    json={'name': 'linkedin_draft',
          'mimeType': 'application/vnd.google-apps.document',
          'parents': [EP_FOLDER]},
    timeout=30
)
li_up = requests.put(init.headers['Location'], data=li_data,
                     headers={'Content-Type': 'text/plain'}, timeout=30)
li_doc_id = li_up.json()['id']
print(f'  ✓ linkedin_draft (Google Doc): https://docs.google.com/document/d/{li_doc_id}/edit')

# Set thumbnail
tok = get_token(DF_REFRESH)
thr = requests.post(
    f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={yt_id}',
    headers={**auth(tok), 'Content-Type': 'image/jpeg'},
    data=THUMB.read_bytes(), timeout=60
)
print(f'  ✓ Thumbnail set: {thr.status_code}')

# ── Save results ──────────────────────────────────────────────────────────────
results = {
    'youtube_video_id': yt_id,
    'youtube_url': f'https://www.youtube.com/watch?v={yt_id}',
    'scheduled': PUBLISH_AT,
    'drive_episode_folder': EP_FOLDER,
    'thumbnail_drive_id': THUMB_DRIVE_ID,
    'thumbnail_url': thumb_url,
    'title': yt_title,
}
(TMP / 'results.json').write_text(json.dumps(results, indent=2))

print('\n══════════════════════════════════════════════════')
print(f'  PIPELINE COMPLETE')
print(f'  Title:      {yt_title}')
print(f'  YouTube:    https://www.youtube.com/watch?v={yt_id}')
print(f'  Scheduled:  Thu 2 Jul 2026 @ 18:00 BST')
print(f'  Drive:      https://drive.google.com/drive/folders/{EP_FOLDER}')
print('══════════════════════════════════════════════════')
print('\n── LINKEDIN DRAFT ────────────────────────────────')
print(linkedin.replace('[VIDEO_URL]', f'https://www.youtube.com/watch?v={yt_id}'))
print('──────────────────────────────────────────────────')
