#!/usr/bin/env python3
"""
Gemini TTS pipeline
1. Downloads narration text from Google Drive
2. Chunks into ~150 words
3. Calls gemini-2.5-flash-preview-tts for each chunk
4. Saves each chunk WAV to disk (resume-safe — skips already-completed chunks)
5. Merges all chunk WAVs into a single WAV + MP3
6. Uploads to Google Drive via OAuth2 (user credentials)
"""

import base64, json, re, time, wave, io, os, sys
import requests

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN_FILE      = "/home/user/ClaudeCode/token.json"
TTS_MODEL       = "gemini-2.5-flash-preview-tts"
VOICE           = "Orus"
CHUNK_WORDS     = 500
SAMPLE_RATE     = 24000
OUTPUT_WAV      = "/home/user/ClaudeCode/narration.wav"
OUTPUT_MP3      = "/home/user/ClaudeCode/narration.mp3"
CHUNKS_DIR      = "/home/user/ClaudeCode/tts_chunks"

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
    tokens = load_tokens()
    key = tokens.get("gemini_tts_api_key") or tokens.get("gemini_api_key", "")
    if not key:
        print("ERROR: gemini_tts_api_key / gemini_api_key is not set in token.json")
        sys.exit(1)
    return key

def get_access_token():
    tokens = load_tokens()
    if "access_token" in tokens:
        r = requests.get(
            "https://www.googleapis.com/oauth2/v1/tokeninfo",
            params={"access_token": tokens["access_token"]}
        )
        if r.ok and r.json().get("expires_in", 0) > 60:
            return tokens["access_token"]

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
    # Check mimeType — Google Docs need the export endpoint
    meta = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=mimeType",
        headers={"Authorization": f"Bearer {token}"}
    )
    meta.raise_for_status()
    mime = meta.json().get("mimeType", "")
    if mime == "application/vnd.google-apps.document":
        r = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=text/plain",
            headers={"Authorization": f"Bearer {token}"}
        )
    else:
        r = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
            headers={"Authorization": f"Bearer {token}"}
        )
    r.raise_for_status()
    return r.content.decode("utf-8")

def drive_delete_existing(token, filename, folder_id):
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
    styled_text = (
        "Read the following aloud as a confident, conversational UK finance narrator. "
        "Steady pace, clear diction, friendly but authoritative. "
        "Consistent tone throughout — no dramatic pauses, no variation in delivery style.\n\n"
        + text
    )
    body = {
        "contents": [{"parts": [{"text": styled_text}]}],
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

def merge_wavs_from_files(chunk_paths, output_path):
    frames, params = b"", None
    for path in chunk_paths:
        with wave.open(path, "rb") as wf:
            if params is None:
                params = wf.getparams()
            frames += wf.readframes(wf.getnframes())
    with wave.open(output_path, "wb") as out:
        out.setparams(params)
        out.writeframes(frames)

def wav_to_mp3(wav_path, mp3_path, bitrate="128k"):
    import subprocess, shutil
    if shutil.which("ffmpeg"):
        subprocess.run(
            ["ffmpeg", "-i", wav_path, "-codec:a", "libmp3lame", "-b:a", bitrate, mp3_path, "-y"],
            check=True, capture_output=True
        )
    else:
        # ffmpeg not available — fall back to pymp3
        import wave, mp3 as pymp3
        with wave.open(wav_path, 'rb') as wf:
            n_ch, rate, frames = wf.getnchannels(), wf.getframerate(), wf.getnframes()
            raw = wf.readframes(frames)
        mode = pymp3.MODE_SINGLE_CHANNEL if n_ch == 1 else pymp3.MODE_JOINT_STEREO
        enc = pymp3.Encoder(open(mp3_path, 'wb'))
        enc.set_channels(n_ch)
        enc.set_sample_rate(rate)
        enc.set_quality(2)
        enc.set_mode(mode)
        chunk = 4096 * n_ch * 2
        for i in range(0, len(raw), chunk):
            enc.write(raw[i:i+chunk])
        enc.flush()

# ── Chunk file helpers ────────────────────────────────────────────────────────
def chunk_path(run_id, i, total):
    digits = len(str(total))
    return os.path.join(CHUNKS_DIR, f"{run_id}_chunk_{str(i).zfill(digits)}.wav")

def chunk_exists(path):
    return os.path.exists(path) and os.path.getsize(path) > 0

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 3:
        print("Usage: python3 run_tts.py <narration_file_id> <output_drive_folder_id> [output_filename]")
        print("Example: python3 run_tts.py 10cIdhUGtCbRqNzPkrMJiardXuOjeKIPI 1Fi6ozVLcf3yW0tCxMEOdn5wOiSVPZhT6 narration.mp3")
        sys.exit(1)

    file_id   = sys.argv[1]
    folder_id = sys.argv[2]
    out_name  = sys.argv[3] if len(sys.argv) > 3 else "narration.mp3"

    # Use file_id as the run identifier so chunks are tied to the narration file
    run_id = file_id[:20]
    os.makedirs(CHUNKS_DIR, exist_ok=True)

    print("Authenticating with Google Drive...")
    token = get_access_token()
    print("  ✓ Authenticated")

    if file_id.startswith("/"):
        print(f"Reading narration from local file: {file_id}...")
        with open(file_id, encoding="utf-8") as f:
            text = f.read()
        print(f"  ✓ {len(text.split())} words read")
    else:
        print(f"Downloading narration from Drive (file: {file_id})...")
        text = drive_download_text(token, file_id)
        print(f"  ✓ {len(text.split())} words downloaded")

    chunks = chunk_text(text)
    total  = len(chunks)
    print(f"  ✓ Split into {total} chunk(s) of ~{CHUNK_WORDS} words")

    # Check which chunks already exist on disk
    existing = [chunk_exists(chunk_path(run_id, i, total)) for i in range(1, total + 1)]
    n_existing = sum(existing)
    if n_existing:
        print(f"  ✓ Resuming — {n_existing}/{total} chunks already on disk, generating remaining {total - n_existing}")

    first_new = True
    for i, chunk in enumerate(chunks, 1):
        path = chunk_path(run_id, i, total)
        if chunk_exists(path):
            print(f"  Chunk {i}/{total} — already done, skipping")
            continue

        if not first_new:
            time.sleep(2)  # paid key — minimal delay between chunks
        first_new = False

        print(f"\nGenerating audio chunk {i}/{total} ({len(chunk.split())} words)...")
        for attempt in range(6):
            try:
                pcm, mime = tts_chunk(chunk)
                rate = SAMPLE_RATE
                m = re.search(r'rate=(\d+)', mime)
                if m:
                    rate = int(m.group(1))
                wav_bytes = pcm_to_wav(pcm, sample_rate=rate)
                with open(path, "wb") as f:
                    f.write(wav_bytes)
                print(f"  ✓ {len(pcm):,} bytes PCM at {rate}Hz → saved to disk")
                break
            except Exception as e:
                if attempt < 5:
                    wait = min(60, 5 * (2 ** attempt))
                    print(f"  Retry in {wait}s... ({e})")
                    time.sleep(wait)
                else:
                    print(f"  Failed after 6 attempts: {e}")
                    print(f"  Chunks 1–{i-1} are saved. Re-run to resume from chunk {i}.")
                    sys.exit(1)

    # All chunks on disk — merge
    chunk_paths = [chunk_path(run_id, i, total) for i in range(1, total + 1)]
    print(f"\nMerging {total} chunks into WAV...")
    merge_wavs_from_files(chunk_paths, OUTPUT_WAV)
    print(f"  ✓ WAV: {os.path.getsize(OUTPUT_WAV):,} bytes")

    print("Converting to MP3...")
    wav_to_mp3(OUTPUT_WAV, OUTPUT_MP3)
    print(f"  ✓ MP3: {os.path.getsize(OUTPUT_MP3):,} bytes")

    upload_path = OUTPUT_WAV if out_name.endswith(".wav") else OUTPUT_MP3
    upload_mime = "audio/wav" if out_name.endswith(".wav") else "audio/mpeg"

    print(f"\nUploading {out_name} to Google Drive...")
    token = get_access_token()
    drive_delete_existing(token, out_name, folder_id)
    result = drive_upload(token, upload_path, out_name, folder_id, mime=upload_mime)
    print(f"  ✓ Uploaded: {result['name']}")
    print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")

    # Clean up chunk files after successful upload
    for path in chunk_paths:
        os.remove(path)
    print(f"  ✓ Chunk files cleaned up")

if __name__ == "__main__":
    main()
