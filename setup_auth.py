#!/usr/bin/env python3"""
One-time OAuth2 setup for Google Drive access.
Run this once: python3 setup_auth.py
It will save a token.json with a refresh token for fully automated future runs.
"""

import json, requests, urllib.parse, webbrowser, sys, os

TOKEN_FILE = "/home/user/ClaudeCode/token.json"
SCOPES = "https://www.googleapis.com/auth/drive"

def load_client_secrets():
    path = "/home/user/ClaudeCode/client_secrets.json"
    if not os.path.exists(path):
        print("ERROR: client_secrets.json not found.")
        print("Follow the setup instructions to create it.")
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    creds = data.get("installed") or data.get("web")
    return creds["client_id"], creds["client_secret"]

def main():
    client_id, client_secret = load_client_secrets()

    params = {
        "client_id": client_id,
        "redirect_uri": "urn:ietf:params:oauth:grant-type:installed_app",
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    print("\n=== Google Drive One-Time Auth Setup ===\n")
    print("1. Open this URL in your browser:\n")
    print(f"   {auth_url}\n")
    print("2. Log in with your Google account and click Allow.")
    print("3. You'll see a code on screen — paste it below.\n")

    code = input("Paste the code here: ").strip()

    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "urn:ietf:params:oauth:grant-type:installed_app",
        "grant_type": "authorization_code",
    })

    if not resp.ok:
        print(f"ERROR: {resp.text}")
        sys.exit(1)

    tokens = resp.json()
    tokens["client_id"] = client_id
    tokens["client_secret"] = client_secret

    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

    print(f"\n✓ Auth complete! Token saved to {TOKEN_FILE}")
    print("You can now run run_tts.py fully automatically.\n")

if __name__ == "__main__":
    main()
