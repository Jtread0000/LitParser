#!/usr/bin/env python3
"""Upload every file in a local directory to a Dropbox folder (overwrite mode).

Used by the fetch-pdfs workflow to push downloaded open-access PDFs into
Dropbox. Self-contained (own token exchange) so it doesn't couple to the
sync script.

Usage: python3 scripts/dropbox_upload_dir.py <local_dir> <dropbox_folder>
Env:   DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

APP_KEY = os.environ["DROPBOX_APP_KEY"]
APP_SECRET = os.environ["DROPBOX_APP_SECRET"]
REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]


def _req(url, data, headers, retries=3):
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, data=data, headers=headers, method="POST"),
                timeout=180,
            ) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"::error title=Dropbox network error::{last}")


def token():
    data = urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN}).encode()
    basic = base64.b64encode(f"{APP_KEY}:{APP_SECRET}".encode()).decode()
    status, body = _req("https://api.dropbox.com/oauth2/token", data,
                        {"Authorization": f"Basic {basic}",
                         "Content-Type": "application/x-www-form-urlencoded"})
    tok = None
    try:
        tok = json.loads(body).get("access_token")
    except Exception:
        pass
    if not tok:
        raise SystemExit(f"::error title=Dropbox token failed::{body.decode(errors='replace')}")
    return tok


def upload(tok, path, data):
    arg = {"path": path, "mode": "overwrite", "mute": True, "autorename": False}
    status, body = _req("https://content.dropboxapi.com/2/files/upload", data,
                        {"Authorization": f"Bearer {tok}",
                         "Dropbox-API-Arg": json.dumps(arg),
                         "Content-Type": "application/octet-stream"})
    if status != 200:
        raise SystemExit(f"::error title=Dropbox upload failed::{path}: {body.decode(errors='replace')}")
    return json.loads(body)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: dropbox_upload_dir.py <local_dir> <dropbox_folder>")
    local_dir, dest_folder = sys.argv[1], sys.argv[2].rstrip("/")
    files = sorted(f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f)))
    if not files:
        print("No files to upload.")
        return
    tok = token()
    for name in files:
        with open(os.path.join(local_dir, name), "rb") as fh:
            meta = upload(tok, f"{dest_folder}/{name}", fh.read())
        print(f"  uploaded {name} -> {meta.get('path_display')} ({meta.get('size')} bytes)")
    print(f"Uploaded {len(files)} file(s) to {dest_folder}")


if __name__ == "__main__":
    main()
