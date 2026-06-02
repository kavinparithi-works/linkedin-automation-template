"""
Run this ONCE locally on your laptop to get your LinkedIn tokens.
It opens a browser, you log in, and it prints the tokens to copy
into your GitHub Secrets.

Usage:
    python get_token.py
"""

import json
import time
import webbrowser
import urllib.parse
import http.server
import threading
import requests

LINKEDIN_AUTH_URL  = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
REDIRECT_URI       = "http://localhost:8989/callback"
SCOPES             = "openid profile w_member_social"

print("=" * 60)
print("  LinkedIn One-Time Token Generator")
print("=" * 60)

client_id     = input("\nPaste your Client ID     : ").strip()
client_secret = input("Paste your Client Secret : ").strip()

auth_code_holder = {}

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in params:
            auth_code_holder["code"] = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Authorization successful! You can close this tab.</h2>")
        else:
            error = params.get("error_description", ["Unknown error"])[0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"<h2>Failed: {error}</h2>".encode())

    def log_message(self, *args):
        pass

server        = http.server.HTTPServer(("localhost", 8989), CallbackHandler)
server_thread = threading.Thread(target=server.handle_request)
server_thread.start()

auth_url = (
    f"{LINKEDIN_AUTH_URL}?response_type=code"
    f"&client_id={client_id}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&scope={urllib.parse.quote(SCOPES)}"
)
print("\nOpening browser — log in and click Allow...")
webbrowser.open(auth_url)

server_thread.join(timeout=120)
server.server_close()

if "code" not in auth_code_holder:
    print("\nERROR: Timed out waiting for callback. Re-run the script.")
    exit(1)

resp = requests.post(
    LINKEDIN_TOKEN_URL,
    data={
        "grant_type":   "authorization_code",
        "code":         auth_code_holder["code"],
        "redirect_uri": REDIRECT_URI,
        "client_id":    client_id,
        "client_secret": client_secret,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
resp.raise_for_status()
data = resp.json()

expires_at         = int(time.time()) + data["expires_in"]
refresh_expires_at = int(time.time()) + data.get("refresh_token_expires_in", 0)

print("\n" + "=" * 60)
print("  SUCCESS — Copy these into GitHub Secrets")
print("=" * 60)
print(f"\n  LI_CLIENT_ID                  = {client_id}")
print(f"  LI_CLIENT_SECRET              = {client_secret}")
print(f"  LI_ACCESS_TOKEN               = {data['access_token']}")
print(f"  LI_ACCESS_TOKEN_EXPIRES_AT    = {expires_at}")
print(f"  LI_REFRESH_TOKEN              = {data.get('refresh_token', '')}")
print(f"  LI_REFRESH_TOKEN_EXPIRES_AT   = {refresh_expires_at}")
print("\n" + "=" * 60)
print("  Go to: GitHub repo → Settings → Secrets and variables")
print("         → Actions → New repository secret")
print("=" * 60 + "\n")
