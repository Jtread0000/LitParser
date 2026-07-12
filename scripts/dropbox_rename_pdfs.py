#!/usr/bin/env python3
"""Rename already-uploaded Lit PDFs in Dropbox to the year-first convention
(<year>-<id>.pdf) and update the pdf: paths in Lit/lit.yaml.

Idempotent: files already matching the convention are left alone. Uses the
Dropbox move endpoint (no re-transfer).

Env: DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN
"""
import base64
import json
import os
import posixpath
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

DB = "Lit/lit.yaml"
APP_KEY = os.environ["DROPBOX_APP_KEY"]
APP_SECRET = os.environ["DROPBOX_APP_SECRET"]
REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]


def _req(url, data, headers, retries=3):
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, data=data, headers=headers, method="POST"),
                timeout=90,
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
    _, body = _req("https://api.dropbox.com/oauth2/token", data,
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


def move(tok, src, dst):
    arg = {"from_path": src, "to_path": dst, "autorename": False, "allow_ownership_transfer": False}
    status, body = _req("https://api.dropboxapi.com/2/files/move_v2", json.dumps(arg).encode(),
                        {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    return status, body


def delete(tok, path):
    status, body = _req("https://api.dropboxapi.com/2/files/delete_v2", json.dumps({"path": path}).encode(),
                        {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    return status, body


def desired_name(rec):
    year = (rec.get("citation") or {}).get("year")
    return f"{year}-{rec['id']}.pdf" if year else f"{rec['id']}.pdf"


def main():
    records = yaml.safe_load(open(DB, encoding="utf-8")) or []
    tok = None
    changed = 0
    pruned = 0
    for rec in records:
        cur = rec.get("pdf")
        if not cur:
            continue
        folder = posixpath.dirname(cur)
        want = f"{folder}/{desired_name(rec)}"
        if cur != want:
            if tok is None:
                tok = token()
            status, body = move(tok, cur, want)
            txt = body.decode(errors="replace")
            if status == 200:
                rec["pdf"] = want
                changed += 1
                print(f"  renamed {posixpath.basename(cur)} -> {posixpath.basename(want)}")
            elif "to/conflict" in txt or "duplicated_or_invalid" in txt:
                # target already exists (already renamed on a prior run); adopt it
                rec["pdf"] = want
                print(f"  target exists, adopting {posixpath.basename(want)}")
            elif "from_lookup/not_found" in txt:
                print(f"  ::warning:: {posixpath.basename(cur)} not found in Dropbox; leaving pdf path as-is")
            else:
                print(f"  ::warning:: move failed for {cur}: {txt}")
            time.sleep(0.3)

        # Prune a stale un-prefixed sibling (<folder>/<id>.pdf) left over from an
        # earlier fetch before the year-first convention. Only when the canonical
        # name carries a year, so bare != canonical.
        bare = f"{folder}/{rec['id']}.pdf"
        if bare != want:
            if tok is None:
                tok = token()
            status, body = delete(tok, bare)
            if status == 200:
                pruned += 1
                print(f"  pruned stale duplicate {posixpath.basename(bare)}")
            elif "path_lookup/not_found" not in body.decode(errors="replace"):
                print(f"  ::warning:: prune check failed for {bare}: {body.decode(errors='replace')}")
            time.sleep(0.3)

    if changed:
        header = ("# Literature database for the Cyber-AI Autonomy study.\n"
                  "# Schema and workflow: see Lit/README.md. Regenerate views: python3 scripts/lit.py\n\n")
        with open(DB, "w", encoding="utf-8") as f:
            f.write(header)
            yaml.safe_dump(records, f, sort_keys=False, allow_unicode=True, width=100)
    print(f"Renamed {changed} file(s) to <year>-<id>.pdf; pruned {pruned} stale duplicate(s).")


if __name__ == "__main__":
    main()
