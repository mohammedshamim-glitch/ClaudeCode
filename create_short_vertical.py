#!/usr/bin/env python3
"""Assemble a vertical 1080x1920 Short from a Short/ subfolder.
- Downloads 00N_short images, short-narration.mp3, short-audio-timings.csv
- Auto-trims each image to its non-white bbox, centres+scales onto 1080x1920 (kills white space)
- Builds per-scene segments (duration from CSV), hard-cut concat
- Burns ALL-CAPS phrase captions (ASS, full 10-field format) in the lower third
- Muxes narration, uploads <name>.mp4 to the Short folder
Usage: python3 create_short_vertical.py <short_folder_id> [output_name.mp4]
"""
import json, requests, subprocess, os, sys, csv
from PIL import Image

SHORT=sys.argv[1]
OUTNAME=sys.argv[2] if len(sys.argv)>2 else 'short.mp4'
W,H=1080,1920
WORK='/tmp/claude-0/-home-user-ClaudeCode/22c2ff02-d450-5c98-a21a-e930c516c570/short_build'
os.makedirs(WORK,exist_ok=True); os.makedirs(WORK+'/seg',exist_ok=True)

t=json.load(open('/home/user/ClaudeCode/token.json'))
at=requests.post('https://oauth2.googleapis.com/token', data={'client_id':t['client_id'],'client_secret':t['client_secret'],'refresh_token':t['refresh_token'],'grant_type':'refresh_token'}).json()['access_token']
HA={'Authorization':f'Bearer {at}'}

def ls(folder):
    out=[]; tok=None
    while True:
        p={'q':f"'{folder}' in parents and trashed=false",'fields':'nextPageToken,files(id,name,mimeType)','pageSize':1000}
        if tok: p['pageToken']=tok
        r=requests.get('https://www.googleapis.com/drive/v3/files',params=p,headers=HA).json()
        out+=r.get('files',[]); tok=r.get('nextPageToken')
        if not tok: break
    return out
def dl(fid,path): open(path,'wb').write(requests.get(f'https://www.googleapis.com/drive/v3/files/{fid}',params={'alt':'media'},headers=HA).content)
def findin(folder,name):
    for f in ls(folder):
        if f['name']==name: return f['id']
    return None

# locate Images subfolder + assets
children=ls(SHORT)
imgfolder=next(f['id'] for f in children if f['mimeType'].endswith('.folder') and f['name'].lower()=='images')
dl(findin(SHORT,'short-narration.mp3'), WORK+'/audio.mp3')
csvtxt=requests.get(f"https://www.googleapis.com/drive/v3/files/{findin(SHORT,'short-audio-timings.csv')}",params={'alt':'media'},headers=HA).content.decode('utf-8')
rows=[r for r in csv.reader([l for l in csvtxt.splitlines() if l.strip()])][1:]  # skip header
# download images
imgs=sorted([f for f in ls(imgfolder) if f['mimeType'].startswith('image/')], key=lambda f:f['name'])
for f in imgs: dl(f['id'], WORK+'/'+f['name'])
print(f'{len(imgs)} images, {len(rows)} timing rows')
assert len(imgs)==len(rows), 'image/timing count mismatch'

def trim_center(src,dst):
    im=Image.open(src).convert('RGB')
    # bbox of non-white (threshold 244)
    from PIL import ImageChops, Image as I
    bg=I.new('RGB',im.size,(255,255,255))
    diff=ImageChops.difference(im,bg).convert('L')
    bbox=diff.point(lambda p:255 if p>12 else 0).getbbox()
    if bbox: im=im.crop(bbox)
    # scale to fit within margins
    maxw,maxh=int(W*0.92),int(H*0.82)
    r=min(maxw/im.width, maxh/im.height)
    im=im.resize((max(1,int(im.width*r)),max(1,int(im.height*r))), I.LANCZOS)
    canvas=I.new('RGB',(W,H),(255,255,255))
    canvas.paste(im,((W-im.width)//2,(H-im.height)//2))
    canvas.save(dst)

# build segments
seglist=open(WORK+'/segs.txt','w')
for i,row in enumerate(rows,1):
    dur=max(float(row[7])-float(row[6]),0.8)
    src=WORK+f'/{i:03d}_short.jpg'
    frame=WORK+f'/f{i:03d}.png'; trim_center(src,frame)
    seg=WORK+f'/seg/s{i:03d}.mp4'
    subprocess.run(['ffmpeg','-y','-loop','1','-i',frame,'-t',f'{dur:.3f}',
        '-vf',f'scale={W}:{H},fps=30,format=yuv420p','-c:v','libx264','-preset','veryfast',seg],
        check=True,capture_output=True)
    seglist.write(f"file '{seg}'\n")
seglist.close()
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',WORK+'/segs.txt','-c','copy',WORK+'/merged.mp4'],check=True,capture_output=True)

# ASS captions — phrase chunks (<=5 words) spread across each scene
def esc(s): return s.replace('\\','\\\\').replace('{','(').replace('}',')')
def ass_time(s):
    cs=int(round(s*100)); h=cs//360000; m=(cs%360000)//6000; sec=(cs%6000)//100; c=cs%100
    return f'{h}:{m:02d}:{sec:02d}.{c:02d}'
header=("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
"[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
"Style: Cap,Liberation Sans,70,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,2,2,60,60,300,1\n\n"
"[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
ev=[]
for i,row in enumerate(rows):
    b=float(row[6]); e=float(row[7]); txt=None
    # reconstruct full scene text from clean script not in CSV excerpt(truncated) -> use excerpt col? col1 truncated to 60. Use it but better: refetch clean.
    ev.append((b,e,i))
# refetch full clean text for accurate captions
clean=requests.get(f"https://www.googleapis.com/drive/v3/files/{findin(SHORT,'short-script-clean.txt')}",params={'alt':'media'},headers=HA).content.decode('utf-8')
scene_txt=[p.strip() for p in clean.split('\n\n') if p.strip()]
lines=[]
for b,e,i in ev:
    words=scene_txt[i].replace('—',' ').split()
    chunks=[' '.join(words[j:j+5]) for j in range(0,len(words),5)]
    span=(e-b)/max(len(chunks),1)
    for k,ch in enumerate(chunks):
        cs=b+k*span; ce=b+(k+1)*span
        lines.append(f"Dialogue: 0,{ass_time(cs)},{ass_time(ce)},Cap,,0,0,0,,{esc(ch.upper())}")
open(WORK+'/subs.ass','w').write(header+'\n'.join(lines)+'\n')

out=WORK+'/'+OUTNAME
subprocess.run(['ffmpeg','-y','-i',WORK+'/merged.mp4','-i',WORK+'/audio.mp3',
    '-filter_complex',f"[0:v]ass={WORK}/subs.ass[v]",'-map','[v]','-map','1:a',
    '-c:v','libx264','-preset','medium','-c:a','aac','-shortest',out],check=True,capture_output=True)
print('built', os.path.getsize(out),'bytes')
# upload
data=open(out,'rb').read()
bnd='===M==='
body=('--'+bnd+'\r\n').encode()+b'Content-Type: application/json; charset=UTF-8\r\n\r\n'+json.dumps({'name':OUTNAME,'parents':[SHORT]}).encode()+b'\r\n'+('--'+bnd+'\r\n').encode()+b'Content-Type: video/mp4\r\n\r\n'+data+b'\r\n'+('--'+bnd+'--').encode()
r=requests.post('https://www.googleapis.com/upload/drive/v3/files',params={'uploadType':'multipart','fields':'id'},headers={'Authorization':f'Bearer {at}','Content-Type':f'multipart/related; boundary={bnd}'},data=body)
print('uploaded', OUTNAME, r.status_code, 'https://drive.google.com/file/d/'+r.json()['id']+'/view')
