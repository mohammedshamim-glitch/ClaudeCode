#!/usr/bin/env python3
"""
Digital Fusion — Video Upload Pipeline
Downloads video from Drive, adds logo overlay, uploads to YouTube scheduled Thursday 6pm BST.
Usage: python3 digital_fusion_upload.py <drive_file_id> <title> <description> [--schedule YYYY-MM-DD]
"""

import json, os, sys, requests, subprocess, tempfile
from datetime import datetime, timedelta

TOKEN_FILE = "/home/user/ClaudeCode/token.json"

DRIVE_FOLDER_ID     = "1MFA1Ooo-KElIRffQRC-TJmTnOytyc-SZ"
PROCESSED_FOLDER_ID = "1q80MPi_hAfcCLeKsYCBOB-_vrBJCV26z"


def load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)


def refresh_access_token(tokens):
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":     tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "refresh_token": tokens["digital_fusion_refresh_token"],
        "grant_type":    "refresh_token",
    })
    return r.json()["access_token"]


def next_thursday_6pm():
    now = datetime.utcnow()
    days_ahead = (3 - now.weekday()) % 7
    if days_ahead < 2:
        days_ahead += 7
    target = now + timedelta(days=days_ahead)
    target = target.replace(hour=17, minute=0, second=0, microsecond=0)  # 17:00 UTC = 18:00 BST
    return target.strftime("%Y-%m-%dT%H:%M:%S+01:00")


def download_video(file_id, dest, access_token):
    print(f"Downloading {file_id}...")
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        params={"alt": "media"},
        headers={"Authorization": f"Bearer {access_token}"},
        stream=True
    )
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            f.write(chunk)
    print(f"  Downloaded: {round(os.path.getsize(dest)/1024/1024, 1)} MB")


def add_logo(input_path, output_path):
    print("Adding Digital Fusion logo...")
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-vf", "drawbox=x=1050:y=668:w=220:h=42:color=black:t=fill,"
               "drawtext=text='Digital Fusion':fontcolor=white:fontsize=24:x=1060:y=676",
        "-c:a", "copy", "-y", output_path
    ], check=True, capture_output=True)
    print(f"  Logo added: {round(os.path.getsize(output_path)/1024/1024, 1)} MB")


def upload_to_youtube(video_path, title, description, tags, publish_at, access_token):
    print("Uploading to YouTube...")
    file_size = os.path.getsize(video_path)
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28",
            "defaultLanguage": "en-GB",
            "defaultAudioLanguage": "en-GB",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": False,
        }
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={**headers, "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4",
                 "X-Upload-Content-Length": str(file_size)},
        json=metadata
    )
    upload_url = r.headers["Location"]
    chunk_size = 5 * 1024 * 1024
    uploaded = 0
    with open(video_path, "rb") as f:
        while uploaded < file_size:
            chunk = f.read(chunk_size)
            r2 = requests.put(upload_url, data=chunk, headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {uploaded}-{uploaded+len(chunk)-1}/{file_size}"
            })
            uploaded += len(chunk)
            print(f"  {round(uploaded/file_size*100)}%", flush=True)
            if r2.status_code in (200, 201):
                result = r2.json()
                print(f"  ✓ Uploaded: https://www.youtube.com/watch?v={result['id']}")
                print(f"  Scheduled: {result['status'].get('publishAt')}")
                return result["id"]


def upload_to_drive(file_path, filename, folder_id, access_token, mime="video/mp4"):
    print(f"Saving to Drive: {filename}")
    file_size = os.path.getsize(file_path)
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
        headers={**headers, "Content-Type": "application/json",
                 "X-Upload-Content-Type": mime,
                 "X-Upload-Content-Length": str(file_size)},
        json={"name": filename, "parents": [folder_id]}
    )
    with open(file_path, "rb") as f:
        data = f.read()
    r2 = requests.put(r.headers["Location"],
        headers={"Content-Type": mime, "Content-Length": str(file_size)}, data=data)
    fid = r2.json()["id"]
    print(f"  ✓ Saved: https://drive.google.com/file/d/{fid}/view")
    return fid


def create_drive_folder(name, parent_id, access_token):
    r = requests.post(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
    )
    return r.json()["id"]


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 digital_fusion_upload.py <drive_file_id> <title> <description>")
        sys.exit(1)

    file_id     = sys.argv[1]
    title       = sys.argv[2]
    description = sys.argv[3]
    tags        = ["Digital Fusion", "tech news", "AI", "technology"]

    tokens = load_tokens()
    access_token = refresh_access_token(tokens)
    publish_at = next_thursday_6pm()
    print(f"Scheduled for: {publish_at}")

    with tempfile.TemporaryDirectory() as tmp:
        original  = os.path.join(tmp, "original.mp4")
        processed = os.path.join(tmp, "processed.mp4")

        download_video(file_id, original, access_token)
        add_logo(original, processed)

        video_id = upload_to_youtube(processed, title, description, tags, publish_at, access_token)

        # Create episode folder in Processed
        slug = title.replace(" ", "_")[:40]
        ep_folder = create_drive_folder(title, PROCESSED_FOLDER_ID, access_token)
        upload_to_drive(original,  f"{slug}_original.mp4",  ep_folder, access_token)
        upload_to_drive(processed, f"{slug}_processed.mp4", ep_folder, access_token)

    print(f"\n✓ Done! YouTube: https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
