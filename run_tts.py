#!/usr/bin/env python3
"""
Gemini TTS pipeline (REST API only — no google-auth SDK dependency)
1. Decodes narration text
2. Chunks into ~150 words
3. Calls gemini-3.1-flash-tts-preview for each chunk
4. Merges PCM audio into a single WAV
5. Uploads WAV to Google Drive via service account JWT
"""

import base64, json, re, struct, time, wave, io, os, sys
import urllib.request, urllib.parse
import requests
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

# ── Config ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY   = "AIzaSyAdTAbkqlNGdTiI-123gAObgRzZfkoqJbs"
CREDS_FILE       = "/home/user/ClaudeCode/service_account.json"
TTS_MODEL        = "gemini-3.1-flash-tts-preview"
VOICE            = "Aoede"
CHUNK_WORDS      = 150
SAMPLE_RATE      = 24000
OUTPUT_WAV       = "/home/user/ClaudeCode/narration.wav"
DRIVE_FOLDER_ID  = "1Fi6ozVLcf3yW0tCxMEOdn5wOiSVPZhT6"   # AI Bubble folder
OUTPUT_FILENAME  = "narration.wav"

# ── Service account JWT auth ──────────────────────────────────────────────────
def get_access_token(creds_file):
    with open(creds_file) as f:
        creds = json.load(f)

    now = int(time.time())
    claim = {
        "iss": creds["client_email"],
        "scope": "https://www.googleapis.com/auth/drive",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }

    header = base64.urlsafe_b64encode(json.dumps({"alg":"RS256","typ":"JWT"}).encode()).rstrip(b"=")
    payload = base64.urlsafe_b64encode(json.dumps(claim).encode()).rstrip(b"=")
    signing_input = header + b"." + payload

    key = RSA.import_key(creds["private_key"].encode())
    h = SHA256.new(signing_input)
    sig = pkcs1_15.new(key).sign(h)
    jwt_token = signing_input + b"." + base64.urlsafe_b64encode(sig).rstrip(b"=")

    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token.decode(),
    })
    resp.raise_for_status()
    return resp.json()["access_token"]

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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{TTS_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}
            }
        }
    }
    resp = requests.post(url, json=body)
    resp.raise_for_status()
    data = resp.json()
    part = data["candidates"][0]["content"]["parts"][0]
    audio_b64 = part["inlineData"]["data"]
    mime     = part["inlineData"]["mimeType"]          # e.g. audio/pcm;rate=24000
    return base64.b64decode(audio_b64), mime

# ── PCM → WAV ────────────────────────────────────────────────────────────────
def pcm_to_wav(pcm_bytes, sample_rate=SAMPLE_RATE, channels=1, sampwidth=2):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()

def merge_wavs(wav_list, output_path):
    all_frames = b""
    params = None
    for w in wav_list:
        buf = io.BytesIO(w)
        with wave.open(buf, "rb") as wf:
            if params is None:
                params = wf.getparams()
            all_frames += wf.readframes(wf.getnframes())
    with wave.open(output_path, "wb") as out:
        out.setparams(params)
        out.writeframes(all_frames)

# ── Drive upload ──────────────────────────────────────────────────────────────
def upload_to_drive(token, local_path, filename, folder_id):
    metadata = json.dumps({"name": filename, "parents": [folder_id]}).encode()
    with open(local_path, "rb") as f:
        audio_data = f.read()

    boundary = b"boundary_xyz_123"
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n" +
        metadata + b"\r\n"
        b"--" + boundary + b"\r\n"
        b"Content-Type: audio/wav\r\n\r\n" +
        audio_data + b"\r\n"
        b"--" + boundary + b"--"
    )

    resp = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary.decode()}",
        },
        data=body,
    )
    if not resp.ok:
        print(f"  Drive error {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    return resp.json()

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Decode narration from base64 (as downloaded from Drive)
    narration_b64 = "VGhlIEFJIGJ1YmJsZSBpcyBkZWZsYXRpbmcuIFRlY2ggc3RvY2tzIHBsdW1tZXRpbmcuIEluc2lkZXJzIGR1bXBpbmcgc2hhcmVzLiBFdmVyeW9uZSBwYW5pY2tlZC4gQnV0IGhlcmUncyB0aGUgdHJ1dGg6IHdoZW4gYmxvb2QgaGl0cyB0aGUgc3RyZWV0cywgdGhhdCdzIHdoZW4gc21hcnQgaW52ZXN0b3JzIGJ1eS4KCkNvbXBhbmllcyBzcGVudCBiaWxsaW9ucyBvbiBBSSBpbmZyYXN0cnVjdHVyZSBleHBlY3RpbmcgbWFzc2l2ZSByZXR1cm5zLiBBZG9wdGlvbiBzbG93ZXIgdGhhbiBleHBlY3RlZC4gQ3VzdG9tZXIgYWNxdWlzaXRpb24gY29zdHMgc2t5cm9ja2V0aW5nLiBQcm9maXQgbWFyZ2lucyBldmFwb3JhdGluZy4gVGhlIHBhcnR5J3Mgb3Zlci4gUmVhbGl0eSBpcyBoaXR0aW5nIGhhcmQuCgpRdWFsaXR5IGNvbXBhbmllcyB3aXRoIHdpZGUgbW9hdHMgYXJlIGdldHRpbmcgY3J1c2hlZCBhbG9uZ3NpZGUgZ2FyYmFnZS4gTWljcm9zb2Z0LCBHb29nbGUsIE5WSURJQeKAlHJlYWwgYnVzaW5lc3NlcyB3aXRoIHJlYWwgZWFybmluZ3MuIFByaWNlcyBhcmUgaXJyYXRpb25hbC4gVGhpcyBpcyB3aGVyZSBmb3J0dW5lcyBhcmUgbWFkZSwgbm90IGxvc3QuCgpEb24ndCBwYW5pYyBidXkgZXZlcnl0aGluZy4gRm9jdXMgb24gY29tcGFuaWVzIHdpdGg6IHN1c3RhaW5hYmxlIGNvbXBldGl0aXZlIGFkdmFudGFnZXMsIHN0cm9uZyBiYWxhbmNlIHNoZWV0cywgYWN0dWFsIHByb2ZpdHMuIExvbmctdGVybSBjb21wb3VuZGluZyBwb3dlci4gRGl2aWRlbmQgZ3Jvd3RoIHBvdGVudGlhbC4gQm9yaW5nLCBzdGFibGUsIHByb2ZpdGFibGUgYnVzaW5lc3Nlcy4KCllvdSBjYW4ndCB0aW1lIHRoZSBib3R0b20gcGVyZmVjdGx5LiBCdXQgeW91IGNhbiBidWlsZCBwb3NpdGlvbnMgc2xvd2x5LiBEb2xsYXItY29zdCBhdmVyYWdpbmcgd29ya3MuIEJ1eSBub3csIGJ1eSBuZXh0IG1vbnRoLCBidXkgaW4gc2l4IG1vbnRocy4gVGltZSBpbiBtYXJrZXQgYmVhdHMgdGltaW5nIHRoZSBtYXJrZXQuCgpJbiAyMDA5LCBpbnZlc3RvcnMgd2hvIGJvdWdodCBkdXJpbmcgcGFuaWMgYmVjYW1lIG1pbGxpb25haXJlcyBieSAyMDIwLiBQYXRpZW5jZSBwYXlzLiBGZWFyIGlzIGEgZmVhdHVyZSwgbm90IGEgYnVnLiBXaGVuIG90aGVycyBmZWFyLCB0aGUgZ3JlZWR5IHByb3NwZXIuIFRoaXMgaXMgeW91ciBtb21lbnQu"
    text = base64.b64decode(narration_b64).decode("utf-8")

    chunks = chunk_text(text)
    print(f"Text split into {len(chunks)} chunk(s):")
    for i, c in enumerate(chunks, 1):
        print(f"  Chunk {i}: {len(c.split())} words")

    wav_chunks = []
    for i, chunk in enumerate(chunks, 1):
        print(f"\nGenerating audio for chunk {i}/{len(chunks)}...")
        for attempt in range(3):
            try:
                pcm, mime = tts_chunk(chunk)
                rate = SAMPLE_RATE
                m = re.search(r'rate=(\d+)', mime)
                if m:
                    rate = int(m.group(1))
                wav_chunks.append(pcm_to_wav(pcm, sample_rate=rate))
                print(f"  ✓ Got {len(pcm):,} bytes PCM at {rate}Hz")
                break
            except Exception as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    print(f"  Retry in {wait}s... ({e})")
                    time.sleep(wait)
                else:
                    print(f"  Failed: {e}")
                    sys.exit(1)

    print(f"\nMerging {len(wav_chunks)} chunk(s) into {OUTPUT_WAV}...")
    merge_wavs(wav_chunks, OUTPUT_WAV)
    print(f"  ✓ WAV written ({os.path.getsize(OUTPUT_WAV):,} bytes)")

    print("\nAuthenticating with Google Drive...")
    token = get_access_token(CREDS_FILE)
    print("  ✓ Access token obtained")

    print(f"Uploading {OUTPUT_FILENAME} to Drive folder {DRIVE_FOLDER_ID}...")
    result = upload_to_drive(token, OUTPUT_WAV, OUTPUT_FILENAME, DRIVE_FOLDER_ID)
    print(f"  ✓ Uploaded! File ID: {result['id']} — Name: {result['name']}")

if __name__ == "__main__":
    main()
