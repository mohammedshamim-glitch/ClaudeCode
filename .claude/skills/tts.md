# TTS Skill — Gemini Text-to-Speech via Google Drive

Convert a narration text file on Google Drive into a merged WAV file using Gemini TTS, then upload the result back to Drive.

## Prerequisites

Install dependencies (once):
```bash
pip install google-generativeai google-api-python-client google-auth pydub
```

Set environment variables:
```bash
export GEMINI_API_KEY="your-gemini-api-key"
export GDRIVE_CREDS_FILE="/path/to/service_account.json"  # Google service account JSON
```

## Usage

```bash
python tts_gemini.py <GOOGLE_DRIVE_FILE_ID> [--output-name narration.wav] [--folder-id <DRIVE_FOLDER_ID>]
```

### Arguments
| Argument | Required | Description |
|---|---|---|
| `file_id` | Yes | Google Drive file ID of the source `.txt` file |
| `--output-name` | No | Name for the output WAV file (default: `narration.wav`) |
| `--folder-id` | No | Drive folder ID to place the output file in |

### Example
```bash
python tts_gemini.py 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs --output-name my_narration.wav --folder-id 1A2B3C4D5E
```

## How it works
1. Downloads the text file from Google Drive
2. Splits text into 150–200 word chunks at sentence boundaries
3. Sends each chunk to Gemini TTS (`gemini-2.5-flash-preview-tts`)
4. Merges all audio chunks into a single WAV file
5. Uploads the WAV back to Google Drive

## Google Drive Setup
You need a **Google Cloud service account** with Drive API access:
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create a service account and download the JSON key
3. Share your Drive folder/file with the service account email
4. Set `GDRIVE_CREDS_FILE` to the path of the downloaded JSON

## Notes
- The script retries each TTS call up to 3 times on failure
- Voice used: `Aoede` (change `voice_name` in `tts_gemini.py` to use others)
- Available voices: Aoede, Charon, Fenrir, Kore, Puck
