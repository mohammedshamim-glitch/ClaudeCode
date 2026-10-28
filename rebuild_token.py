#!/usr/bin/env python3
"""
Rebuilds token.json and client_secrets.json from environment variables
stored in ~/.claude/settings.json. Runs automatically via PreToolUse hook.
Only writes files if they don't already exist or are missing keys.
"""
import json, os, requests

TOKEN_FILE = "/home/user/ClaudeCode/token.json"
SECRETS_FILE = "/home/user/ClaudeCode/client_secrets.json"

client_id     = os.environ.get("GOOGLE_CLIENT_ID", "")
client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
drive_rt      = os.environ.get("GOOGLE_DRIVE_REFRESH_TOKEN", "")
yt_rt         = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")
gemini_key    = os.environ.get("GEMINI_API_KEY", "")

if not all([client_id, client_secret, drive_rt, yt_rt, gemini_key]):
    exit(0)  # env vars not set yet, skip silently

def needs_rebuild(path, required_keys):
    if not os.path.exists(path):
        return True
    try:
        with open(path) as f:
            data = json.load(f)
        return not all(k in data for k in required_keys)
    except Exception:
        return True

# Rebuild token.json
if needs_rebuild(TOKEN_FILE, ["refresh_token", "youtube_refresh_token", "gemini_api_key"]):
    # Get a fresh Drive access token
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": drive_rt, "grant_type": "refresh_token"
    })
    access_token = r.json().get("access_token", "") if r.ok else ""

    token = {
        "access_token": access_token,
        "refresh_token": drive_rt,
        "youtube_refresh_token": yt_rt,
        "gemini_api_key": gemini_key,
        "client_id": client_id,
        "client_secret": client_secret,
        "token_type": "Bearer"
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(token, f, indent=2)

# Rebuild client_secrets.json
if needs_rebuild(SECRETS_FILE, ["installed"]):
    secrets = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }
    with open(SECRETS_FILE, "w") as f:
        json.dump(secrets, f, indent=2)
