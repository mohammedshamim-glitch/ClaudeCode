#!/usr/bin/env python3
"""
Gemini TTS pipeline
1. Downloads narration text from Google Drive
2. Chunks into ~150 words
3. Calls gemini-2.5-flash-preview-tts for each chunk
4. Merges PCM audio into a single WAV + MP3
5. Uploads to Google Drive via OAuth2 (user credentials)
"""

import base64, json, re, time, wave, io, os, sys
import requests

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN_FILE      = "/home/user/ClaudeCode/token.json"
TTS_MODEL       = "gemini-2.5-flash-preview-tts"
VOICE           = "Orus"
CHUNK_WORDS     = 150
SAMPLE_RATE     = 24000
OUTPUT_WAV      = "/home/user/ClaudeCode/narration.wav"
OUTPUT_MP3      = "/home/user/ClaudeCode/narration.mp3"

# ── OAuth2 token management ───────────────────────────────────────────────────
def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        print("ERROR: token.json not found. Run setup_auth.py first.")
        sys.exit(1)
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

def get_gemini_api_key():
    key = load_tokens().get("gemini_api_key", "")
    if not key:
        print("ERROR: gemini_api_key is not set in token.json")
        sys.exit(1)
    return key

def get_access_token():
    tokens = load_tokens()
    if "access_token" in tokens:
        # Quick check if token is still valid
        r = requests.get(
            "https://www.googleapis.com/oauth2/v1/tokeninfo",
            params={"access_token": tokens["access_token"]}
        )
        if r.ok and r.json().get("expires_in", 0) > 60:
            return tokens["access_token"]

    # Refresh the token
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":     tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "refresh_token": tokens["refresh_token"],
        "grant_type":    "refresh_token",
    })
    if not r.ok:
        print(f"ERROR refreshing token: {r.text}")
        sys.exit(1)
    new_tokens = r.json()
    tokens["access_token"] = new_tokens["access_token"]
    save_tokens(tokens)
    return tokens["access_token"]

# ── Google Drive helpers ──────────────────────────────────────────────────────
def drive_download_text(token, file_id):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    return r.text

def drive_delete_existing(token, filename, folder_id):
    """Delete any existing files with this name in the folder before uploading."""
    r = requests.get(
        "https://www.googleapis.com/drive/v3/files",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "q": f"'{folder_id}' in parents and name='{filename}' and trashed=false",
            "fields": "files(id,name)",
        },
    )
    r.raise_for_status()
    for f in r.json().get("files", []):
        requests.delete(
            f"https://www.googleapis.com/drive/v3/files/{f['id']}",
            headers={"Authorization": f"Bearer {token}"},
        ).raise_for_status()
        print(f"  ✓ Deleted existing {f['name']}")

def drive_upload(token, local_path, filename, folder_id, mime="audio/wav"):
    with open(local_path, "rb") as f:
        data = f.read()
    metadata = json.dumps({"name": filename, "parents": [folder_id]}).encode()
    boundary = b"tts_boundary_xyz"
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n" +
        metadata + b"\r\n"
        b"--" + boundary + b"\r\n" +
        f"Content-Type: {mime}\r\n\r\n".encode() +
        data + b"\r\n"
        b"--" + boundary + b"--"
    )
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary.decode()}",
        },
        data=body,
    )
    if not r.ok:
        print(f"  Drive upload error {r.status_code}: {r.text}")
    r.raise_for_status()
    return r.json()

# ── Text chunking ─────────────────────────────────────────────────────────────
def chunk_text(text, max_words=CHUNK_WORDS):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks, current, count = [], [], 0
    for s in sentences:
        w = len(s.split())
        if count + w > max_words and count > 0:
            chunks.append(" ".join(current))
            current, count = [s], w
        else:
            current.append(s)
            count += w
    if current:
        chunks.append(" ".join(current))
    return chunks

# ── Gemini TTS ────────────────────────────────────────────────────────────────
def tts_chunk(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{TTS_MODEL}:generateContent?key={get_gemini_api_key()}"
    body = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}
            }
        }
    }
    r = requests.post(url, json=body)
    r.raise_for_status()
    part = r.json()["candidates"][0]["content"]["parts"][0]
    audio_b64 = part["inlineData"]["data"]
    mime      = part["inlineData"]["mimeType"]
    return base64.b64decode(audio_b64), mime

# ── Audio helpers ─────────────────────────────────────────────────────────────
def pcm_to_wav(pcm_bytes, sample_rate=SAMPLE_RATE, channels=1, sampwidth=2):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()

def merge_wavs(wav_list, output_path):
    frames, params = b"", None
    for w in wav_list:
        with wave.open(io.BytesIO(w), "rb") as wf:
            if params is None:
                params = wf.getparams()
            frames += wf.readframes(wf.getnframes())
    with wave.open(output_path, "wb") as out:
        out.setparams(params)
        out.writeframes(frames)

def wav_to_mp3(wav_path, mp3_path, bitrate="128k"):
    import subprocess
    subprocess.run(
        ["ffmpeg", "-i", wav_path, "-codec:a", "libmp3lame", "-b:a", bitrate, mp3_path, "-y"],
        check=True, capture_output=True
    )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print("Usage: python3 run_tts.py <narration_file_id> <output_drive_folder_id> [output_filename]")
        print("Example: python3 run_tts.py 10cIdhUGtCbRqNzPkrMJiardXuOjeKIPI 1Fi6ozVLcf3yW0tCxMEOdn5wOiSVPZhT6 narration.mp3")
        sys.exit(1)

    file_id   = sys.argv[1]
    folder_id = sys.argv[2]
    out_name  = sys.argv[3] if len(sys.argv) > 3 else "narration.mp3"

    print("Authenticating with Google Drive...")
    token = get_access_token()
    print("  ✓ Authenticated")

    print(f"Downloading narration from Drive (file: {file_id})...")
    text = drive_download_text(token, file_id)
    print(f"  ✓ {len(text.split())} words downloaded")

    chunks = chunk_text(text)
    print(f"  ✓ Split into {len(chunks)} chunk(s) of ~{CHUNK_WORDS} words")

    wav_chunks = []
    for i, chunk in enumerate(chunks, 1):
        if i > 1:
            time.sleep(8)  # inter-chunk delay to stay within rate limits
        print(f"\nGenerating audio chunk {i}/{len(chunks)} ({len(chunk.split())} words)...")
        for attempt in range(6):
            try:
                pcm, mime = tts_chunk(chunk)
                rate = SAMPLE_RATE
                m = re.search(r'rate=(\d+)', mime)
                if m:
                    rate = int(m.group(1))
                wav_chunks.append(pcm_to_wav(pcm, sample_rate=rate))
                print(f"  ✓ {len(pcm):,} bytes PCM at {rate}Hz")
                break
            except Exception as e:
                if attempt < 5:
                    wait = min(60, 5 * (2 ** attempt))
                    print(f"  Retry in {wait}s... ({e})")
                    time.sleep(wait)
                else:
                    print(f"  Failed after 6 attempts: {e}")
                    sys.exit(1)

    print(f"\nMerging audio into WAV...")
    merge_wavs(wav_chunks, OUTPUT_WAV)
    print(f"  ✓ WAV: {os.path.getsize(OUTPUT_WAV):,} bytes")

    print("Converting to MP3...")
    wav_to_mp3(OUTPUT_WAV, OUTPUT_MP3)
    print(f"  ✓ MP3: {os.path.getsize(OUTPUT_MP3):,} bytes")

    # Upload MP3 (or WAV if name ends in .wav)
    upload_path = OUTPUT_WAV if out_name.endswith(".wav") else OUTPUT_MP3
    upload_mime = "audio/wav" if out_name.endswith(".wav") else "audio/mpeg"

    print(f"\nUploading {out_name} to Google Drive...")
    token = get_access_token()  # refresh if needed
    drive_delete_existing(token, out_name, folder_id)
    result = drive_upload(token, upload_path, out_name, folder_id, mime=upload_mime)
    print(f"  ✓ Uploaded: {result['name']}")
    print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")

if __name__ == "__main__":
    main()
