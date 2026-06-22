#!/usr/bin/env python3
"""Generate styled LinkedIn images using PIL and upload to Drive folders."""

import json, requests, io, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'token.json')
with open(TOKEN_FILE) as f:
    tok = json.load(f)

REFRESH_TOKEN = tok['digital_fusion_refresh_token']
CLIENT_ID = tok['client_id']
CLIENT_SECRET = tok['client_secret']

W, H = 1200, 630  # LinkedIn optimal image size

TOPICS = [
    {
        'slug': 'the-unseen-ai-military-might-and-your-disappearing-privacy',
        'folder_id': '13781WAsBW1Ndg6GuqOw9SB_yW3kL_BQZ',
        'style': 'surveillance',
        'line1': 'THE UNSEEN AI',
        'line2': 'Military Might &',
        'line3': 'Your Disappearing Privacy',
        'bg_color': (8, 15, 30),
        'accent': (0, 120, 255),
        'highlight': (255, 60, 60),
    },
    {
        'slug': 'nfts-the-digital-mirage-that-crumbled',
        'folder_id': '1dcwPW4rFItaVBHzOLubDgQcHJQXYNRBH',
        'style': 'crash',
        'line1': 'NFTs',
        'line2': 'The Digital Mirage',
        'line3': 'That Crumbled',
        'bg_color': (15, 5, 25),
        'accent': (180, 0, 220),
        'highlight': (255, 50, 50),
    },
    {
        'slug': 'ais-great-deception-more-hoax-than-hype',
        'folder_id': '1cnQi3nqVo_unB4T5CAy2aIWlBPsvwEiO',
        'style': 'robot',
        'line1': "AI'S GREAT DECEPTION",
        'line2': 'More Hoax',
        'line3': 'Than Hype',
        'bg_color': (5, 20, 20),
        'accent': (0, 200, 180),
        'highlight': (255, 200, 0),
    },
    {
        'slug': 'ais-650-billion-illusion-the-tech-buildout-is-collapsing',
        'folder_id': '18vHjyUw1sv2T8KqeqRdH2ZxlEwrTt0xA',
        'style': 'collapse',
        'line1': "AI'S £650 BILLION ILLUSION",
        'line2': 'The Tech Buildout',
        'line3': 'Is Collapsing',
        'bg_color': (5, 10, 25),
        'accent': (0, 100, 255),
        'highlight': (255, 80, 0),
    },
]


def find_font(size):
    """Try common font paths, fall back to default."""
    paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def draw_grid(draw, w, h, color, spacing=60, alpha=40):
    """Draw a perspective grid on a dark background."""
    c = color + (alpha,)
    for x in range(0, w + spacing, spacing):
        draw.line([(x, 0), (x, h)], fill=c, width=1)
    for y in range(0, h + spacing, spacing):
        draw.line([(0, y), (w, y)], fill=c, width=1)


def draw_camera_icon(draw, cx, cy, size, color):
    """Draw a simple surveillance camera shape."""
    # Camera body
    draw.rectangle([cx - size//2, cy - size//4, cx + size//3, cy + size//4],
                   outline=color, width=3)
    # Lens circle
    draw.ellipse([cx + size//3 - size//6, cy - size//6, cx + size//3 + size//6, cy + size//6],
                 outline=color, width=3)
    # Mount bar
    draw.rectangle([cx - size//2 - size//8, cy - size//3, cx - size//2 + 4, cy - size//4],
                   fill=color)
    draw.rectangle([cx - size//2 - size//8, cy - size//3, cx - size//2 - size//8 + size//4, cy - size//3 + 4],
                   fill=color)


def draw_eye_scan(draw, cx, cy, radius, color, alpha=80):
    """Draw a scanning eye / radar circle."""
    for i in range(4, 0, -1):
        r = radius * i // 4
        c = color + (alpha // i,)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=2)
    # Crosshair
    draw.line([(cx - radius, cy), (cx + radius, cy)], fill=color + (alpha,), width=1)
    draw.line([(cx, cy - radius), (cx, cy + radius)], fill=color + (alpha,), width=1)


def draw_bar_chart_crash(draw, x, y, w, h, accent, highlight):
    """Draw a bar chart with crashing bars (right side lower)."""
    bar_w = w // 7
    heights = [0.85, 0.90, 0.80, 0.70, 0.50, 0.30, 0.15]
    colors = [accent] * 4 + [highlight] * 3
    for i, (frac, col) in enumerate(zip(heights, colors)):
        bh = int(h * frac)
        bx = x + i * (bar_w + 4)
        by = y + h - bh
        draw.rectangle([bx, by, bx + bar_w, y + h], fill=col + (200,))


def draw_circuit(draw, cx, cy, size, color, alpha=60):
    """Draw circuit board lines."""
    c = color + (alpha,)
    pts = [
        (cx, cy), (cx + size, cy), (cx + size, cy - size//2),
        (cx + size + size//2, cy - size//2),
    ]
    draw.line(pts, fill=c, width=2)
    draw.ellipse([cx + size + size//2 - 6, cy - size//2 - 6,
                  cx + size + size//2 + 6, cy - size//2 + 6], fill=c)

    pts2 = [(cx, cy), (cx - size//2, cy), (cx - size//2, cy + size//3)]
    draw.line(pts2, fill=c, width=2)
    draw.ellipse([cx - size//2 - 5, cy + size//3 - 5,
                  cx - size//2 + 5, cy + size//3 + 5], fill=c)


def draw_server_racks(draw, x, y, w, h, accent, crumble=False):
    """Draw server rack silhouettes."""
    rack_w = w // 5
    for i in range(5):
        rx = x + i * (rack_w + 6)
        rh = h - (i * h // 10 if crumble else 0)
        ry = y + h - rh
        col = accent if i < 3 else (180, 40, 0)
        draw.rectangle([rx, ry, rx + rack_w, y + h], outline=col + (180,), width=2)
        # Unit lines
        for j in range(1, 8):
            ly = ry + j * rh // 8
            draw.line([(rx + 4, ly), (rx + rack_w - 4, ly)], fill=col + (100,), width=1)
            # LED dot
            led_col = (0, 255, 100) if i < 3 else (255, 60, 0)
            draw.ellipse([rx + 8, ly - 3, rx + 14, ly + 3], fill=led_col + (200,))


def make_image(topic):
    """Create a styled 1200x630 LinkedIn image for a topic."""
    bg = topic['bg_color']
    accent = topic['accent']
    highlight = topic['highlight']
    style = topic['style']

    img = Image.new('RGBA', (W, H), bg + (255,))
    draw = ImageDraw.Draw(img, 'RGBA')

    # Background gradient (darker left, slightly lighter right)
    for x in range(W):
        alpha = int(30 * x / W)
        draw.line([(x, 0), (x, H)], fill=(bg[0] + alpha//4, bg[1] + alpha//4, bg[2] + alpha//3, 255))

    # Style-specific background elements
    if style == 'surveillance':
        draw_grid(draw, W, H, accent, spacing=50, alpha=25)
        # Scanning circles (right side)
        for r, a in [(200, 20), (140, 35), (80, 55), (40, 80)]:
            draw.ellipse([W - 280 - r, H//2 - r, W - 280 + r, H//2 + r],
                         outline=accent + (a,), width=2)
        # Crosshair
        draw.line([(W - 280, H//2 - 220), (W - 280, H//2 + 220)], fill=accent + (50,), width=1)
        draw.line([(W - 280 - 220, H//2), (W - 280 + 220, H//2)], fill=accent + (50,), width=1)
        # Camera icons (scattered)
        for cx, cy, sz in [(W - 280, H//2, 70), (W - 450, H//4, 45), (W - 150, H*3//4, 40)]:
            draw_camera_icon(draw, cx, cy, sz, accent + (150,))
        # Scan line
        draw.line([(W - 280 - 195, H//2 + 5), (W - 280, H//2 + 5)], fill=highlight + (120,), width=2)
        draw.line([(W - 280 - 195, H//2 + 5), (W - 280 - 200, H//2 - 3)], fill=highlight + (120,), width=2)

    elif style == 'crash':
        # Crypto chart crash (right side)
        draw_bar_chart_crash(draw, W - 380, H//4, 340, H//2, accent, highlight)
        # Shatter lines emanating from center-right
        cx, cy = W - 200, H//2
        for angle in range(0, 360, 25):
            rad = math.radians(angle)
            length = random.randint(60, 200)
            ex = cx + int(length * math.cos(rad))
            ey = cy + int(length * math.sin(rad))
            draw.line([(cx, cy), (ex, ey)], fill=highlight + (40,), width=1)
        # Bitcoin-like hex grid
        for i in range(6):
            r = 40 + i * 25
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=accent + (30,), width=1)
        # Down arrows
        for ax in [W - 150, W - 250]:
            draw.polygon([(ax, H*2//3), (ax - 20, H*2//3 - 40), (ax + 20, H*2//3 - 40)],
                         fill=highlight + (180,))
        draw.rectangle([0, 0, 8, H], fill=highlight + (200,))

    elif style == 'robot':
        # Circuit board elements (right side)
        for ox, oy in [(W - 350, 80), (W - 200, 150), (W - 400, 300), (W - 180, 380)]:
            draw_circuit(draw, ox, oy, 60, accent, alpha=80)
        # Robot face outline (hexagonal)
        cx, cy = W - 250, H//2
        size = 130
        hex_pts = [(cx + int(size * math.cos(math.radians(a))),
                    cy + int(size * math.sin(math.radians(a)))) for a in range(0, 360, 60)]
        draw.polygon(hex_pts, outline=accent + (120,), width=3)
        # Eyes
        for ex in [cx - 45, cx + 45]:
            draw.ellipse([ex - 20, cy - 40, ex + 20, cy], outline=accent + (180,), width=3)
            draw.ellipse([ex - 8, cy - 28, ex + 8, cy - 12], fill=accent + (200,))
        # Crack line through face
        draw.line([(cx - 10, cy - size + 20), (cx + 30, cy), (cx - 20, cy + size - 30)],
                  fill=highlight + (160,), width=3)
        # Scan grid overlay
        draw_grid(draw, W, H, accent, spacing=40, alpha=15)

    elif style == 'collapse':
        # Server racks (right side, crumbling)
        draw_server_racks(draw, W - 400, H//6, 360, H*2//3, accent, crumble=True)
        # Financial graph collapsing
        pts = [(W - 400, H//3), (W - 320, H//4), (W - 240, H//3 + 20),
               (W - 160, H*2//3), (W - 80, H*5//6)]
        draw.line(pts, fill=highlight + (200,), width=3)
        # Data flow lines
        for i in range(8):
            y = H//6 + i * H//10
            draw.line([(W//2, y), (W//2 + 40, y)], fill=accent + (60,), width=1)
        draw_grid(draw, W, H, accent, spacing=45, alpha=18)

    # Left panel: dark overlay for text legibility
    for x in range(W * 2 // 3):
        alpha = int(180 * (1 - x / (W * 2 // 3)))
        draw.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))

    # Left accent bar
    draw.rectangle([0, 0, 6, H], fill=highlight + (255,))

    # Load fonts
    f_big = find_font(62)
    f_med = find_font(46)
    f_small = find_font(36)
    f_tag = find_font(22)

    # Top tag
    draw.text((30, 30), 'DIGITAL FUSION', font=f_tag, fill=accent + (220,))

    # Main title lines
    l1 = topic['line1']
    l2 = topic['line2']
    l3 = topic['line3']

    y_start = H//2 - 110
    draw.text((28, y_start - 2), l1, font=f_big, fill=(255, 255, 255, 255))
    draw.text((28, y_start + 72), l2, font=f_med, fill=highlight + (255,))
    draw.text((28, y_start + 125), l3, font=f_med, fill=(220, 220, 220, 255))

    # Bottom divider line
    draw.line([(28, H - 70), (W * 3//5, H - 70)], fill=accent + (100,), width=1)

    # Bottom tag
    tag = 'Finance · Technology · Analysis'
    draw.text((28, H - 55), tag, font=f_tag, fill=(160, 160, 180, 200))

    return img.convert('RGB')


def get_access_token():
    r = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token',
    })
    r.raise_for_status()
    return r.json()['access_token']


def upload_to_drive(access_token, folder_id, filename, img_bytes):
    meta = {'name': filename, 'parents': [folder_id]}
    mime = 'image/jpeg'
    init_r = requests.post(
        'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Upload-Content-Type': mime,
            'X-Upload-Content-Length': str(len(img_bytes)),
        },
        json=meta,
        timeout=30,
    )
    if not init_r.ok:
        print(f'  Upload init failed: {init_r.status_code} {init_r.text[:200]}')
        return None

    loc = init_r.headers['Location']
    up = requests.put(
        loc,
        headers={'Content-Type': mime, 'Content-Length': str(len(img_bytes))},
        data=img_bytes,
        timeout=120,
    )
    if up.ok:
        return up.json().get('id')
    print(f'  Upload PUT failed: {up.status_code} {up.text[:200]}')
    return None


def main():
    print('Getting Drive access token...')
    access_token = get_access_token()

    for topic in TOPICS:
        print(f'\n--- {topic["slug"]} ---')
        print('  Generating image...')
        img = make_image(topic)

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=92)
        img_bytes = buf.getvalue()

        filename = topic['slug'] + '.jpg'
        print(f'  Size: {len(img_bytes):,} bytes. Uploading as "{filename}"...')
        file_id = upload_to_drive(access_token, topic['folder_id'], filename, img_bytes)
        if file_id:
            print(f'  Uploaded: https://drive.google.com/file/d/{file_id}/view')
        else:
            print('  Upload FAILED.')

    print('\nAll done.')


if __name__ == '__main__':
    main()
