#!/usr/bin/env python3
"""Convert fetched PDFs to Markdown (free, deterministic, zero-token) so papers
can be read/searched cheaply and are reusable across sessions.

For each lit.yaml record that has a `pdf` (a Dropbox path) but no `Lit/md/<id>.md`
yet, download the PDF from Dropbox, convert it with pymupdf4llm, save the markdown
under Lit/md/ (git-tracked), and record `md:` in lit.yaml.

Runs in the cloud Action (downloads via the Dropbox token). It also runs locally
if the token env vars are set. For complex 2-column journal PDFs where this
extractor garbles the layout, regenerate that one .md with pdf2md-claude on the
Mac (see Lit/README.md).

Env: DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN
"""
import base64
import json
import os
import posixpath
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

DB = "Lit/lit.yaml"
MD_DIR = "Lit/md"
SRC_MARK = "<!-- source-pdf -->"


def source_header(rec):
    """A small generated block linking the Markdown back to its source PDF in
    Dropbox. The URL is Dropbox's own "open this file" web link — it opens the PDF
    for whoever is logged into that Dropbox account (no shared link, no exposure)."""
    pdf = rec.get("pdf") or ""
    folder = posixpath.dirname(pdf)
    fn = posixpath.basename(pdf)
    url = f"https://www.dropbox.com/home{folder}?preview={urllib.parse.quote(fn)}"
    return (f"{SRC_MARK}\n"
            f"> **Source PDF:** [{fn}]({url})  \n"
            f"> **Dropbox path:** `{pdf}`  \n"
            f"> **Record:** `{rec['id']}` — see `Lit/lit.yaml`\n\n---\n\n")


def _req(url, data, headers, retries=3):
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, data=data, headers=headers, method="POST"),
                timeout=120,
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
        {"grant_type": "refresh_token", "refresh_token": os.environ["DROPBOX_REFRESH_TOKEN"]}).encode()
    basic = base64.b64encode(
        f"{os.environ['DROPBOX_APP_KEY']}:{os.environ['DROPBOX_APP_SECRET']}".encode()).decode()
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


def download(tok, path):
    status, body = _req("https://content.dropboxapi.com/2/files/download", None,
                        {"Authorization": f"Bearer {tok}",
                         "Dropbox-API-Arg": json.dumps({"path": path})})
    return body if status == 200 else None


def main():
    import pymupdf4llm  # imported here so --check-style callers get a clear error
    os.makedirs(MD_DIR, exist_ok=True)
    records = yaml.safe_load(open(DB, encoding="utf-8")) or []
    tok = None
    converted = 0
    for rec in records:
        pdf = rec.get("pdf")
        if not pdf:
            continue
        md_path = f"{MD_DIR}/{rec['id']}.md"
        if os.path.exists(md_path):
            if rec.get("md") != md_path:
                rec["md"] = md_path
            continue
        if tok is None:
            tok = token()
        data = download(tok, pdf)
        if not data:
            print(f"  ::warning:: could not download {pdf}")
            continue
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tf.write(data)
            tmp = tf.name
        try:
            md = pymupdf4llm.to_markdown(tmp)
        except Exception as e:
            print(f"  ::warning:: convert failed for {rec['id']}: {e}")
            os.unlink(tmp)
            continue
        os.unlink(tmp)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(source_header(rec) + md)
        rec["md"] = md_path
        converted += 1
        print(f"  md   {rec['id']} ({len(md)//1000}k chars) -> {md_path}")

    header = ("# Literature database for the Cyber-AI Autonomy study.\n"
              "# Schema and workflow: see Lit/README.md. Regenerate views: python3 scripts/lit.py\n\n")
    with open(DB, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(records, f, sort_keys=False, allow_unicode=True, width=100)
    with_md = sum(1 for r in records if r.get("md"))
    print(f"Converted {converted} new; {with_md} of {len(records)} records now have markdown.")


if __name__ == "__main__":
    main()
