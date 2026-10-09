#!/usr/bin/env python3
"""
Keep an n8n "NotebookLM API" credential fresh from a notebooklm-py session.

Each run:
  1. `notebooklm auth refresh --verify` rotates Google's short-lived session cookie and checks that the
     refreshed cookies still sign in (skip with --no-refresh).
  2. The Google cookies of the notebooklm-py session file are written into the credential's
     "Session JSON" field through the n8n API (PATCH /api/v1/credentials/{id}).

Run it every 15-20 minutes from cron or a systemd timer.

Environment:
  N8N_URL             base URL of n8n, for example http://localhost:5678 (use a private address:
                      the cookies are sent to this URL)
  N8N_API_KEY         n8n API key (Settings -> n8n API)
  N8N_CREDENTIAL_ID   ID of the "NotebookLM API" credential (shown in the credential page URL)
  NOTEBOOKLM_STORAGE  optional, defaults to ~/.notebooklm/profiles/default/storage_state.json

Options:
  --no-refresh   skip `notebooklm auth refresh`
  --dry-run      prepare and check everything but do not call n8n

Exit code 0 on success, 1 on any failure (with a short message). Cookie values are never printed.
Needs only the Python standard library and, unless --no-refresh is used, the `notebooklm` command.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

REQUIRED = ("SID", "__Secure-1PSIDTS")
GOOGLE_HOST = re.compile(r"^(?:.*\.)?google\.[a-z]{2,3}(?:\.[a-z]{2})?$")


def fail(message):
    print("ERROR: " + message)
    sys.exit(1)


def refresh_session():
    exe = shutil.which("notebooklm")
    if not exe:
        fail("the `notebooklm` command was not found (pip install \"notebooklm-py[browser]\"), or use --no-refresh")
    try:
        result = subprocess.run([exe, "auth", "refresh", "--verify"], capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        fail("`notebooklm auth refresh` did not finish within 240 s")
    if result.returncode != 0:
        tail = " ".join((result.stdout + " " + result.stderr).split())[-200:]
        fail("the session could not be refreshed or no longer signs in (exit %d); sign in again with "
             "`notebooklm login`. Detail: %s" % (result.returncode, tail))


def build_session_json(storage_path):
    try:
        with open(storage_path, encoding="utf-8") as handle:
            state = json.load(handle)
    except (OSError, ValueError) as exc:
        fail("cannot read the session file %s: %s" % (storage_path, exc))
    now = time.time()
    kept = []
    for cookie in state.get("cookies", []):
        host = str(cookie.get("domain", "")).lstrip(".").lower()
        if not GOOGLE_HOST.match(host):
            continue
        expires = cookie.get("expires", -1)
        if isinstance(expires, (int, float)) and 0 < expires < now:
            continue
        kept.append(cookie)
    names = {cookie.get("name") for cookie in kept}
    missing = [name for name in REQUIRED if name not in names]
    if missing:
        fail("the session has no valid %s cookie; sign in again with `notebooklm login`" % ", ".join(missing))
    return json.dumps({"cookies": kept, "origins": []}, ensure_ascii=False, separators=(",", ":")), len(kept)


def update_credential(base_url, api_key, credential_id, session_json):
    request = urllib.request.Request(
        "%s/api/v1/credentials/%s" % (base_url.rstrip("/"), credential_id),
        method="PATCH",
        data=json.dumps({"data": {"sessionJson": session_json}}).encode("utf-8"),
        # Some proxies (Cloudflare) reject Python's default User-Agent.
        headers={"X-N8N-API-KEY": api_key, "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": "curl/8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.status != 200:
                fail("n8n answered HTTP %d" % response.status)
    except urllib.error.HTTPError as exc:
        detail = " ".join(exc.read().decode("utf-8", "ignore").split())[:160]
        fail("n8n refused the update: HTTP %d %s" % (exc.code, detail))
    except (urllib.error.URLError, OSError) as exc:
        fail("cannot reach n8n at %s: %s" % (base_url, exc))


def main():
    dry_run = "--dry-run" in sys.argv
    storage = os.path.expanduser(os.environ.get("NOTEBOOKLM_STORAGE", "~/.notebooklm/profiles/default/storage_state.json"))
    base_url = os.environ.get("N8N_URL", "")
    api_key = os.environ.get("N8N_API_KEY", "")
    credential_id = os.environ.get("N8N_CREDENTIAL_ID", "")
    if not dry_run and not (base_url and api_key and credential_id):
        fail("set N8N_URL, N8N_API_KEY and N8N_CREDENTIAL_ID")
    if "--no-refresh" not in sys.argv:
        refresh_session()
    session_json, count = build_session_json(storage)
    if dry_run:
        print("dry run: %d Google cookies ready, nothing was sent to n8n" % count)
        return
    update_credential(base_url, api_key, credential_id, session_json)
    print("n8n credential %s updated with %d cookies" % (credential_id, count))


if __name__ == "__main__":
    main()
