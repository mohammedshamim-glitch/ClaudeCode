#!/usr/bin/env python3
"""
One-time YouTube OAuth2 setup.
Run this once: python3 setup_youtube_auth.py
Adds youtube_refresh_token to token.json for automated future uploads.
"""

import json, requests, urllib.parse, sys, os

TOKEN_FILE = "/home/user/ClaudeCode/token.json"
SCOPE = "https://www.googleapis.com/auth/youtube https://www.googleapis.com/auth/youtube.force-ssl"

def main():
    with open(TOKEN_FILE) as f:
        tokens = json.load(f)

    client_id     = tokens["client_id"]
    client_secret = tokens["client_secret"]

    params = {
        "client_id":     client_id,
        "redirect_uri":  "http://localhost",
        "response_type": "code",
        "scope":         SCOPE,
        "access_type":   "offline",
        "prompt":        "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    print("\n=== YouTube One-Time Auth Setup ===\n")
    print("1. Open this URL in your browser:\n")
    print(f"   {auth_url}\n")
    print("2. Log in with your Google account and click Allow.")
    print("3. Your browser will redirect to localhost and show an error.")
    print("   Copy the full URL from the address bar.")
    print("   It looks like: http://localhost/?code=4/XXXX...&scope=...\n")

    raw = input("Paste the redirect URL or code here: ").strip()
    if "code=" in raw:
        code = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query).get("code", [raw])[0]
    else:
        code = raw

    r = requests.post("https://oauth2.googleapis.com/token", data={
        "code":          code,
        "client_id":     client_id,
        "client_secret": client_secret,
        "redirect_uri":  "http://localhost",
        "grant_type":    "authorization_code",
    })

    if not r.ok:
        print(f"ERROR: {r.text}")
        sys.exit(1)

    data = r.json()
    tokens["youtube_refresh_token"] = data["refresh_token"]
    tokens["youtube_access_token"]  = data.get("access_token", "")

    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

    print(f"\n✓ YouTube auth complete! Token saved to {TOKEN_FILE}")
    print("You can now run upload_youtube.py fully automatically.\n")

if __name__ == "__main__":
    main()
