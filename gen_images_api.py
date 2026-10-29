#!/usr/bin/env python3
"""
Monkey Finance — API image generator with BUILT-IN validation + auto re-roll.

Purpose: get every image right FIRST TIME so nothing needs fixing after.
Enforces, per image, in the REQUEST (so the model can't drift):
  - generationConfig.imageConfig.aspectRatio  ("16:9" main/thumbnail, "9:16" Short)
  - pure-white background line in the prompt
  - £-only line + character-reference anchors passed as input parts
And VALIDATES every returned image before saving, re-rolling in place on failure:
  - dimensions match the target orientation (not square / not wrong aspect)
  - background corners are near-pure-white (no grey/blue wash)
On save it also runs a whiten pass (flatten >=238 to pure 255) as a final safety net.
Batches of 10 then sleeps 60s (rate limits).

Usage:
  python3 gen_images_api.py <prompts_file> <out_dir> --slug salary --aspect 16:9 \
      [--model gemini-2.5-flash-image] [--anchors Monkey-mascot.webp,Sarah.webp] \
      [--thumbnail]  (single prompt -> thumbnail.jpg, forces Pro + 16:9)

Prompts file = the 04-image-prompts.txt / short-image-prompts.txt format:
an optional header, a '===' divider, then one blank-line-separated prompt per scene,
each starting with its scene number.
"""
import json, requests, os, sys, time, re, argparse, base64, io
from PIL import Image
import numpy as np

TOKEN='/home/user/ClaudeCode/token.json'
CHAR_REF_FOLDER='1ObdWnyzOsU6pOCvbd-I_bdDjShcC-yps'  # Character References
FLASH='gemini-2.5-flash-image'
PRO='gemini-3-pro-image'
WHITE_LINE=("Pure flat #FFFFFF white background that fills the entire frame edge to edge, "
            "with absolutely no tint, gradient, vignette, grey wash or drop shadow. "
            "CRITICAL: do NOT draw an actual whiteboard object or any kind of frame around the scene — "
            "no rectangular whiteboard panel, no grey or coloured border, no outline box, no tray, "
            "no marker rail and no rounded corners. The illustration bleeds straight to all four edges on plain white.")
MONEY_LINE=("CRITICAL: show money only in UK pounds using the £ symbol. "
            "ABSOLUTELY NO $ (dollar) or € (euro) symbols anywhere. No real company or person names on canvas.")
TEXT_LINE=("TEXT STYLE: any text, words, numbers, labels or arrows written on the canvas must be a SINGLE solid colour — "
           "bold BLACK by default, or bold RED only for a key stat/warning. NEVER use multicoloured, rainbow, or "
           "per-letter-different-colour lettering (it looks gimmicky and childish). Keep all lettering clean, consistent and legible.")
# Flash holds a reference image loosely, so reinforce the mascot outfit in TEXT too (where Flash listens
# reliably) — otherwise the green suit drifts to other colours, esp. in multi-anchor / unusual-pose scenes.
MONKEY_LINE=("MASCOT CONSISTENCY: whenever the Monkey appears, it ALWAYS wears its signature bright GREEN business suit "
             "with a matching green tie and a gold 'M' lapel badge, exactly matching the reference image. "
             "NEVER change the suit to grey, blue, brown or any other colour.")

t=json.load(open(TOKEN))
KEY=t.get('gemini_tts_api_key') or t.get('gemini_api_key')
def drive_token():
    return requests.post('https://oauth2.googleapis.com/token',data={'client_id':t['client_id'],
        'client_secret':t['client_secret'],'refresh_token':t['refresh_token'],
        'grant_type':'refresh_token'}).json()['access_token']

def load_anchor_b64(name, at):
    """Fetch a character-reference image from Drive, return (mime,b64)."""
    r=requests.get('https://www.googleapis.com/drive/v3/files',
        params={'q':f"'{CHAR_REF_FOLDER}' in parents and name='{name}' and trashed=false",
                'fields':'files(id,name,mimeType)'},headers={'Authorization':f'Bearer {at}'}).json()
    f=r['files'][0]
    data=requests.get(f"https://www.googleapis.com/drive/v3/files/{f['id']}",params={'alt':'media'},
        headers={'Authorization':f'Bearer {at}'}).content
    return f['mimeType'], base64.b64encode(data).decode()

def whiten(im, thresh=234):
    # Flatten near-white background to pure #FFFFFF with a soft ramp so anti-aliased
    # edges don't halo. thresh=234 cleans the typical 230-242 model wash while keeping
    # bold illustration colour (whose min channel sits well below 220). Applied on SAVE.
    a=np.asarray(im.convert('RGB')).astype('float32'); mn=a.min(axis=2)
    out=a.copy(); out[mn>=thresh]=255.0
    lo=thresh-16; band=(mn>=lo)&(mn<thresh)
    f=((mn[band]-lo)/(thresh-lo))[:,None]; out[band]=a[band]*(1-f)+255.0*f
    return Image.fromarray(np.clip(out,0,255).astype('uint8'))

def validate(im, aspect):
    """Return (ok, reason). Re-roll only on hard failures: wrong orientation/aspect,
    or a PERVASIVE background wash (even the whitest corner is tinted). Mild tint is
    left to the save-whiten pass, so good images (e.g. content near a corner) still pass."""
    w,h=im.size
    ratio=max(w,h)/min(w,h)
    if abs(w-h) < 0.08*max(w,h):  return False, f'square {w}x{h}'
    if aspect=='16:9' and w<=h:   return False, f'not landscape {w}x{h}'
    if aspect=='9:16' and h<=w:   return False, f'not portrait {w}x{h}'
    if ratio < 1.4:               return False, f'aspect too square {w}x{h} ({ratio:.2f})'
    a=np.asarray(im.convert('RGB'))
    corners=[a[:40,:40],a[:40,-40:],a[-40:,:40],a[-40:,-40:]]
    mins=[int(c.reshape(-1,3).mean(0).min()) for c in corners]
    if max(mins) < 232:           # whitest corner still tinted -> pervasive wash
        return False, f'pervasive grey wash corners min={mins}'
    return True, 'ok'

def gen_one(prompt, aspect, model, anchor_parts, retries=2):
    body_parts=[{"text": prompt+"\n\n"+WHITE_LINE+"\n"+MONEY_LINE+"\n"+TEXT_LINE+"\n"+MONKEY_LINE}]+anchor_parts
    payload={"contents":[{"parts":body_parts}],
             "generationConfig":{"responseModalities":["IMAGE"],
                                 "imageConfig":{"aspectRatio":aspect}}}
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={KEY}'
    for attempt in range(retries+1):
        r=requests.post(url,json=payload,timeout=180)
        if r.status_code!=200:
            if r.status_code in (429,503) and attempt<retries:
                time.sleep(30); continue
            raise RuntimeError(f'API {r.status_code}: {r.text[:200]}')
        parts=r.json()['candidates'][0]['content']['parts']
        b64=next((p['inlineData']['data'] for p in parts if 'inlineData' in p), None)
        if not b64:
            if attempt<retries: continue
            raise RuntimeError('no image in response')
        im=Image.open(io.BytesIO(base64.b64decode(b64))).convert('RGB')
        ok,reason=validate(im, aspect)
        if ok:
            return whiten(im), attempt
        print(f'      re-roll ({reason})')
    # final attempt failed validation -> return last with whiten, flag
    return whiten(im), -1

def parse_prompts(path):
    txt=open(path,encoding='utf-8').read()
    if '===' in txt: txt=txt.split('===',1)[1]
    blocks=[b.strip() for b in txt.split('\n\n') if b.strip() and re.match(r'^\d+\s',b.strip())]
    return blocks

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('prompts'); ap.add_argument('out_dir')
    ap.add_argument('--slug',required=True)
    ap.add_argument('--aspect',default='16:9',choices=['16:9','9:16'])
    ap.add_argument('--model',default=FLASH)
    ap.add_argument('--anchors',default='Monkey.webp')
    ap.add_argument('--suffix',default='')   # e.g. _short
    ap.add_argument('--thumbnail',action='store_true')
    ap.add_argument('--only',default='')      # comma scene numbers to (re)gen only
    # Flash image (Nano Banana) Tier-1 limit is 500 RPM / 500K TPM / 2000 RPD — huge.
    # Sequential gen uses <1% of that, so default to a tiny courtesy pause, not 60s.
    ap.add_argument('--sleep',type=float,default=1.0)  # seconds between batches
    ap.add_argument('--batch',type=int,default=25)     # pause every N images
    a=ap.parse_args()
    os.makedirs(a.out_dir,exist_ok=True)
    at=drive_token()
    anchors=[]
    for nm in [x for x in a.anchors.split(',') if x.strip()]:
        mime,b64=load_anchor_b64(nm.strip(),at)
        anchors.append({"inline_data":{"mime_type":mime,"data":b64}})
    print(f'{len(anchors)} anchor(s); model={a.model}; aspect={a.aspect}')
    if a.thumbnail:
        prompt=open(a.prompts,encoding='utf-8').read().strip()
        im,att=gen_one(prompt,'16:9',PRO,anchors)
        p=os.path.join(a.out_dir,'thumbnail.jpg'); im.save(p,quality=92)
        print(f'thumbnail -> {p} ({im.size}) {"OK" if att>=0 else "VALIDATION FAILED - review"}')
        return
    prompts=parse_prompts(a.prompts)
    only=set(int(x) for x in a.only.split(',') if x.strip()) if a.only else None
    print(f'{len(prompts)} prompts')
    failed=[]
    for i,block in enumerate(prompts,1):
        n=int(re.match(r'^(\d+)',block).group(1))
        if only and n not in only: continue
        im,att=gen_one(block,a.aspect,a.model,anchors)
        fn=f'{n:03d}{a.suffix or ("_"+a.slug)}.jpg'
        p=os.path.join(a.out_dir,fn); im.save(p,quality=92)
        flag='' if att>=0 else '  <-- VALIDATION FAILED, review'
        print(f'  {fn} {im.size}{flag}')
        if att<0: failed.append(n)
        if a.sleep>0 and i%a.batch==0 and i<len(prompts):
            print(f'  ...{a.batch} done, pausing {a.sleep}s'); time.sleep(a.sleep)
    print('DONE.', f'{len(failed)} need manual review: {failed}' if failed else 'all validated OK.')

if __name__=='__main__':
    main()
