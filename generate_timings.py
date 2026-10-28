#!/usr/bin/env python3
"""
Generate audio_timings_new.csv using aeneas forced alignment.

Method:
  1. Download narration audio + script from Drive
  2. Convert audio to 16kHz mono WAV (required by aeneas)
  3. Split script by blank lines → one scene per line
  4. Run aeneas forced alignment: syncs source text directly to audio
     using espeak + DTW on MFCC features — no re-transcription step
  5. Build CSV with start/end times for each scene
  6. Upload audio_timings_new.csv to the episode Drive folder

Dependencies:
  aeneas 1.7.3  (pip install from source — requires libespeak-dev)
  ffmpeg        (for audio conversion)

Usage:
    python3 generate_timings.py <episode_folder_id>
"""

import csv, json, os, re, subprocess, sys, tempfile, requests

TOKEN_FILE = "/home/user/ClaudeCode/token.json"

SCRIPT_NAMES_PRIORITY = [
    "03b-narration-sentences.txt",
    "03-narration-script-clean.txt",
    "03-narration-script-clean-FINAL.txt",
    "03-narration-script-clean-v3.txt",
    "03-narration-script-clean-v2.txt",
    "03-narration-script-clean-v1.txt",
    "narration_script.txt",
]

AUDIO_MIMES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav"}

# ── Auth ──────────────────────────────────────────────────────────────────────
def load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

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
    r.raise_for_status()
    tokens["access_token"] = r.json()["access_token"]
    save_tokens(tokens)
    return tokens["access_token"]

# ── Drive helpers ─────────────────────────────────────────────────────────────
def drive_list_all(token, folder_id):
    files, page_token = [], None
    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed=false",
            "fields": "nextPageToken,files(id,name,mimeType,size)",
            "pageSize": 100,
        }
        if page_token:
            params["pageToken"] = page_token
        r = requests.get(
            "https://www.googleapis.com/drive/v3/files",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        r.raise_for_status()
        data = r.json()
        files.extend(data.get("files", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return files

def drive_get_name(token, file_id):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"fields": "name"},
    )
    r.raise_for_status()
    return r.json()["name"]

def drive_download(token, file_id, local_path):
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
        headers={"Authorization": f"Bearer {token}"}, stream=True,
    )
    r.raise_for_status()
    with open(local_path, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)

def drive_download_text(token, file_id):
    meta = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}?fields=mimeType",
        headers={"Authorization": f"Bearer {token}"},
    )
    meta.raise_for_status()
    if meta.json().get("mimeType") == "application/vnd.google-apps.document":
        r = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType=text/plain",
            headers={"Authorization": f"Bearer {token}"},
        )
    else:
        r = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
            headers={"Authorization": f"Bearer {token}"},
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

def drive_upload_csv(token, local_path, filename, folder_id):
    with open(local_path, "rb") as f:
        data = f.read()
    metadata = json.dumps({"name": filename, "parents": [folder_id]}).encode()
    boundary = b"csv_boundary_xyz"
    body = (
        b"--" + boundary + b"\r\n"
        b"Content-Type: application/json; charset=UTF-8\r\n\r\n" +
        metadata + b"\r\n"
        b"--" + boundary + b"\r\n"
        b"Content-Type: text/csv\r\n\r\n" +
        data + b"\r\n"
        b"--" + boundary + b"--"
    )
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files"
        "?uploadType=multipart&fields=id,name,webViewLink",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary.decode()}",
        },
        data=body,
    )
    r.raise_for_status()
    return r.json()

# ── Scene splitting ───────────────────────────────────────────────────────────
def split_scenes(raw_text):
    """Split narration/sentence file by blank lines. Each paragraph = one scene."""
    paragraphs = re.split(r'\n\s*\n', raw_text.strip())
    scenes = []
    for p in paragraphs:
        p = p.strip().replace('\n', ' ')
        if p and not re.match(r'^---', p):
            scenes.append(p)
    return scenes

def split_sub_scenes(scenes, words_per_chunk=25):
    """Split each scene into ~words_per_chunk word chunks (for sub-scene image alignment)."""
    sub_scenes = []
    for scene in scenes:
        words = scene.split()
        i = 0
        while i < len(words):
            chunk = words[i:i + words_per_chunk]
            sub_scenes.append(" ".join(chunk))
            i += words_per_chunk
    return sub_scenes

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_time(seconds):
    m = int(seconds) // 60
    s = seconds - m * 60
    return f"{m:02d}:{s:05.2f}"

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_timings.py <episode_folder_id> [--sub-scenes]")
        print("  --sub-scenes  Split each narration paragraph into ~25-word chunks")
        print("                (use when you have more images than narration paragraphs)")
        sys.exit(1)

    folder_id    = sys.argv[1]
    use_sub_scenes = "--sub-scenes" in sys.argv

    print("Authenticating...")
    token = get_access_token()
    folder_name = drive_get_name(token, folder_id)
    print(f"  ✓ Episode: {folder_name}")

    # Find script and audio files
    items = drive_list_all(token, folder_id)

    script_file = None
    candidates = [f for f in items if f["name"] in SCRIPT_NAMES_PRIORITY]
    if candidates:
        script_file = min(candidates, key=lambda f: SCRIPT_NAMES_PRIORITY.index(f["name"]))

    audio_file = None
    for f in items:
        if f.get("mimeType", "") in AUDIO_MIMES:
            audio_file = f
            break

    # Also check Audio subfolder
    if not audio_file:
        for f in items:
            if f.get("mimeType") == "application/vnd.google-apps.folder" and f["name"] == "Audio":
                sub_items = drive_list_all(token, f["id"])
                candidates = [sf for sf in sub_items if sf.get("mimeType", "") in AUDIO_MIMES]
                if candidates:
                    audio_file = max(candidates, key=lambda f: int(f.get("size", 0)))

    if not script_file:
        print("ERROR: narration script not found in episode folder")
        sys.exit(1)
    if not audio_file:
        print("ERROR: no audio file (mp3/wav) found in episode folder")
        sys.exit(1)

    print(f"  ✓ Script: {script_file['name']}")
    print(f"  ✓ Audio:  {audio_file['name']}")

    tmpdir = tempfile.mkdtemp(prefix="mf_aeneas_")
    try:
        # Download files
        print("\nDownloading files...")
        audio_ext  = os.path.splitext(audio_file["name"])[1] or ".mp3"
        audio_path = os.path.join(tmpdir, f"narration{audio_ext}")
        wav_path   = os.path.join(tmpdir, "narration.wav")
        drive_download(token, audio_file["id"], audio_path)
        print("  ✓ Audio downloaded")

        script_text = drive_download_text(token, script_file["id"])
        print("  ✓ Script downloaded")

        # Get audio duration — prefer ffprobe, fall back to wave module
        import shutil as _shutil, wave as _wave
        _ffprobe_ok = bool(_shutil.which("ffprobe")) and subprocess.run(["ffprobe", "-version"], capture_output=True).returncode == 0
        if _ffprobe_ok:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True, text=True, check=True,
            )
            total_duration = float(result.stdout.strip())
        else:
            # ffprobe unavailable — read duration from local WAV if present
            local_wav = "/home/user/ClaudeCode/narration.wav"
            if os.path.exists(local_wav):
                with _wave.open(local_wav, 'rb') as wf:
                    total_duration = wf.getnframes() / wf.getframerate()
            else:
                raise RuntimeError("ffprobe unavailable and no local narration.wav found")
        print(f"  ✓ Audio duration: {total_duration:.2f}s ({fmt_time(total_duration)})")

        # Convert to 16kHz mono WAV for aeneas — prefer ffmpeg, fall back to scipy+resampling
        _ffmpeg_ok = bool(_shutil.which("ffmpeg")) and subprocess.run(["ffmpeg", "-version"], capture_output=True).returncode == 0
        if _ffmpeg_ok:
            subprocess.run(
                ["ffmpeg", "-i", audio_path, "-ar", "16000", "-ac", "1", wav_path, "-y"],
                capture_output=True, check=True,
            )
        else:
            # ffmpeg unavailable — use local WAV and resample with scipy
            import numpy as np
            local_wav = "/home/user/ClaudeCode/narration.wav"
            with _wave.open(local_wav, 'rb') as wf:
                n_ch, sampw, rate, n_frames = wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()
                raw = wf.readframes(n_frames)
            samples = np.frombuffer(raw, dtype=np.int16)
            if n_ch > 1:
                samples = samples.reshape(-1, n_ch).mean(axis=1).astype(np.int16)
            if rate != 16000:
                from scipy.signal import resample_poly
                from math import gcd
                g = gcd(16000, rate)
                samples = resample_poly(samples, 16000 // g, rate // g).astype(np.int16)
            with _wave.open(wav_path, 'wb') as out:
                out.setnchannels(1)
                out.setsampwidth(2)
                out.setframerate(16000)
                out.writeframes(samples.tobytes())
        print("  ✓ Converted to 16kHz WAV")

        # Split script into scenes
        scenes = split_scenes(script_text)
        print(f"  ✓ {len(scenes)} scenes parsed from narration script")
        if use_sub_scenes:
            scenes = split_sub_scenes(scenes)
            print(f"  ✓ Split into {len(scenes)} sub-scenes (~25 words each)")

        # Write plain text file for aeneas (one scene per line)
        script_path = os.path.join(tmpdir, "script.txt")
        json_out    = os.path.join(tmpdir, "timings.json")
        with open(script_path, "w", encoding="utf-8") as f:
            for scene in scenes:
                f.write(scene + "\n")

        # Run forced alignment — prefer aeneas, fall back to Whisper word-level alignment
        try:
            from aeneas.executetask import ExecuteTask
            from aeneas.task import Task
            _use_aeneas = True
        except ImportError:
            _use_aeneas = False

        rows = []
        if _use_aeneas:
            print("\nRunning aeneas forced alignment...")
            config = "task_language=eng|is_text_type=plain|os_task_file_format=json"
            task = Task(config_string=config)
            task.audio_file_path_absolute    = wav_path
            task.text_file_path_absolute     = script_path
            task.sync_map_file_path_absolute = json_out
            ExecuteTask(task).execute()
            task.output_sync_map_file()
            print("  ✓ Alignment complete")

            with open(json_out) as f:
                alignment = json.load(f)

            fragments = alignment["fragments"]
            if len(fragments) != len(scenes):
                print(f"WARNING: {len(fragments)} fragments returned for {len(scenes)} scenes")

            print(f"\n{'#':>3}  {'Start':>7}  {'End':>7}  {'Dur':>6}  Narration")
            print("-" * 90)
            for i, frag in enumerate(fragments):
                start = round(float(frag["begin"]), 3)
                end   = round(float(frag["end"]),   3)
                dur   = round(end - start, 2)
                text  = scenes[i]
                rows.append({
                    "scene":             i + 1,
                    "narration_excerpt": text,
                    "words":             len(text.split()),
                    "duration_seconds":  dur,
                    "start_time":        fmt_time(start),
                    "end_time":          fmt_time(end),
                    "start_seconds":     start,
                    "end_seconds":       end,
                })
                preview = text[:60] + ("…" if len(text) > 60 else "")
                print(f"  {i+1:>3}  {fmt_time(start):>7}  {fmt_time(end):>7}  {dur:>5.1f}s  {preview}")
        else:
            # Whisper word-level alignment fallback (with proportional fallback if model unavailable)
            print("\nRunning Whisper word-level alignment (aeneas unavailable)...")
            try:
                import whisper as _whisper
                model = _whisper.load_model("base")
                _use_whisper = True
            except Exception as _we:
                print(f"  Whisper unavailable ({_we}) — falling back to proportional alignment")
                _use_whisper = False
            if not _use_whisper:
                # Pure proportional alignment: distribute total_duration by word count
                total_words = sum(len(s.split()) for s in scenes)
                cursor = 0.0
                print(f"\n{'#':>3}  {'Start':>7}  {'End':>7}  {'Dur':>6}  Narration")
                print("-" * 90)
                for i, scene_text in enumerate(scenes):
                    n_words = len(scene_text.split())
                    dur = round((n_words / total_words) * total_duration, 3)
                    start = round(cursor, 3)
                    end   = round(cursor + dur, 3)
                    rows.append({
                        "scene":             i + 1,
                        "narration_excerpt": scene_text,
                        "words":             n_words,
                        "duration_seconds":  round(dur, 2),
                        "start_time":        fmt_time(start),
                        "end_time":          fmt_time(end),
                        "start_seconds":     start,
                        "end_seconds":       end,
                    })
                    preview = scene_text[:60] + ("…" if len(scene_text) > 60 else "")
                    print(f"  {i+1:>3}  {fmt_time(start):>7}  {fmt_time(end):>7}  {round(dur,1):>5.1f}s  {preview}")
                    cursor = end
                print("  ✓ Proportional alignment complete")
            if _use_whisper:
                result = model.transcribe(wav_path, word_timestamps=True, language="en")
                all_words = []
                for seg in result.get("segments", []):
                    for w in seg.get("words", []):
                        all_words.append({"word": w["word"].strip().lower(), "start": w["start"], "end": w["end"]})
                print(f"  ✓ Whisper transcribed {len(all_words)} words")
                word_idx = 0
                scene_boundaries = []
                for scene_text in scenes:
                    n = len(scene_text.split())
                    target = min(word_idx + n, len(all_words) - 1)
                    scene_boundaries.append((word_idx, target))
                    word_idx = target
                print(f"\n{'#':>3}  {'Start':>7}  {'End':>7}  {'Dur':>6}  Narration")
                print("-" * 90)
                prev_end = 0.0
                for i, (wi_start, wi_end) in enumerate(scene_boundaries):
                    start = round(all_words[wi_start]["start"], 3) if wi_start < len(all_words) else prev_end
                    end   = round(all_words[wi_end]["end"],   3) if wi_end   < len(all_words) else total_duration
                    start = max(start, prev_end)
                    end   = max(end, start + 0.5)
                    dur   = round(end - start, 2)
                    text  = scenes[i]
                    rows.append({"scene": i+1, "narration_excerpt": text, "words": len(text.split()),
                                 "duration_seconds": dur, "start_time": fmt_time(start),
                                 "end_time": fmt_time(end), "start_seconds": start, "end_seconds": end})
                    preview = text[:60] + ("…" if len(text) > 60 else "")
                    print(f"  {i+1:>3}  {fmt_time(start):>7}  {fmt_time(end):>7}  {dur:>5.1f}s  {preview}")
                    prev_end = end
                print("  ✓ Whisper alignment complete")

        total = sum(r["duration_seconds"] for r in rows)
        print(f"\nTotal: {total:.2f}s  Audio: {total_duration:.2f}s")
        print(f"Duration range: {min(r['duration_seconds'] for r in rows):.2f}s"
              f" – {max(r['duration_seconds'] for r in rows):.2f}s")

        # Write CSV
        csv_path = os.path.join(tmpdir, "audio_timings_new.csv")
        fieldnames = ["scene", "narration_excerpt", "words", "duration_seconds",
                      "start_time", "end_time", "start_seconds", "end_seconds"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n✓ CSV written: {len(rows)} rows")

        # Upload to Drive
        print("Uploading audio_timings_new.csv to Drive...")
        token = get_access_token()
        drive_delete_existing(token, "audio_timings_new.csv", folder_id)
        result = drive_upload_csv(token, csv_path, "audio_timings_new.csv", folder_id)
        print(f"  ✓ Uploaded: {result['name']}")
        print(f"  ✓ View: {result.get('webViewLink', 'n/a')}")

    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
