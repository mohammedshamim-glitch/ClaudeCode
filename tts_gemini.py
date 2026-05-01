#!/usr/bin/env python3
"""
Gemini TTS Skill
- Downloads a text file from Google Drive
- Chunks it into 150-200 word segments
- Sends each chunk to Gemini TTS API
- Merges audio chunks into a single WAV file
- Uploads the result back to Google Drive
"""

import os
import sys
import wave
import struct
import tempfile
import argparse
import io
import re
import time

import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.service_account import Credentials

# ── Config ────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"
GDRIVE_CREDS_FILE = os.environ.get("GDRIVE_CREDS_FILE", "service_account.json")
SCOPES = ["https://www.googleapis.com/auth/drive"]

CHUNK_MIN_WORDS = 150
CHUNK_MAX_WORDS = 200

# ── Text chunking ─────────────────────────────────────────────────────────────

def chunk_text(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current_words = []
    current_count = 0

    for sentence in sentences:
        words = sentence.split()
        word_count = len(words)

        if current_count + word_count > CHUNK_MAX_WORDS and current_count >= CHUNK_MIN_WORDS:
            chunks.append(" ".join(current_words))
            current_words = words
            current_count = word_count
        else:
            current_words.extend(words)
            current_count += word_count

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks

# ── Google Drive helpers ──────────────────────────────────────────────────────

def get_drive_service():
    creds = Credentials.from_service_account_file(GDRIVE_CREDS_FILE, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

def download_text_file(service, file_id: str) -> str:
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue().decode("utf-8")

def upload_wav_file(service, local_path: str, filename: str, parent_folder_id: str = None):
    metadata = {"name": filename}
    if parent_folder_id:
        metadata["parents"] = [parent_folder_id]
    media = MediaFileUpload(local_path, mimetype="audio/wav")
    uploaded = service.files().create(body=metadata, media_body=media, fields="id,name").execute()
    return uploaded

# ── Gemini TTS ────────────────────────────────────────────────────────────────

def text_to_wav_bytes(client, text: str) -> bytes:
    response = client.models.generate_content(
        model=GEMINI_TTS_MODEL,
        contents=text,
        config={
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": "Aoede"}
                }
            },
        },
    )
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    return audio_data

# ── WAV merge ─────────────────────────────────────────────────────────────────

def merge_wav_files(wav_bytes_list: list[bytes], output_path: str):
    frames_all = b""
    params = None

    for wav_bytes in wav_bytes_list:
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            if params is None:
                params = wf.getparams()
            frames_all += wf.readframes(wf.getnframes())

    with wave.open(output_path, "wb") as out:
        out.setparams(params)
        out.writeframes(frames_all)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gemini TTS: Drive text → WAV → Drive")
    parser.add_argument("file_id", help="Google Drive file ID of the source text file")
    parser.add_argument("--output-name", default="narration.wav", help="Output WAV filename on Drive")
    parser.add_argument("--folder-id", default=None, help="Google Drive folder ID to upload the result into")
    args = parser.parse_args()

    if not GEMINI_API_KEY:
        print("ERROR: Set the GEMINI_API_KEY environment variable.")
        sys.exit(1)

    print("Connecting to Google Drive...")
    drive = get_drive_service()

    print(f"Downloading file {args.file_id}...")
    text = download_text_file(drive, args.file_id)
    print(f"Downloaded {len(text.split())} words.")

    chunks = chunk_text(text)
    print(f"Split into {len(chunks)} chunks.")

    genai.configure(api_key=GEMINI_API_KEY)
    client = genai.Client() if hasattr(genai, "Client") else genai

    wav_chunks = []
    for i, chunk in enumerate(chunks, 1):
        print(f"Generating audio for chunk {i}/{len(chunks)} ({len(chunk.split())} words)...")
        for attempt in range(3):
            try:
                wav_bytes = text_to_wav_bytes(client, chunk)
                wav_chunks.append(wav_bytes)
                break
            except Exception as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    print(f"  Retrying in {wait}s... ({e})")
                    time.sleep(wait)
                else:
                    print(f"  Failed after 3 attempts: {e}")
                    sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    print(f"Merging {len(wav_chunks)} audio chunks...")
    merge_wav_files(wav_chunks, tmp_path)

    print(f"Uploading {args.output_name} to Google Drive...")
    result = upload_wav_file(drive, tmp_path, args.output_name, args.folder_id)
    print(f"Done! Uploaded as '{result['name']}' (id: {result['id']})")

    os.unlink(tmp_path)

if __name__ == "__main__":
    main()
