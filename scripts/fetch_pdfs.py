#!/usr/bin/env python3
"""Fetch open-access PDFs for the literature database — legally.

Resolution order per record:
  * arXiv preprint     -> direct PDF from arxiv.org
  * DOI-bearing item   -> Unpaywall (finds a legal open-access copy, if one exists)
  * otherwise          -> flagged for manual retrieval (gray lit / paywalled)

This NEVER touches library proxies, logins, or paywalled full text. Paywalled
items with no open-access copy are listed for you to download by hand through
your library, in your own browser (the terms-of-service-clean way). Once you
drop such a PDF into the Dropbox _Lit/pdfs/ folder and record its pdf: path in
lit.yaml, the conversion step picks it up like any other.

Usage:
  python3 scripts/fetch_pdfs.py --dry-run                     # report OA coverage
  python3 scripts/fetch_pdfs.py --target ~/Dropbox/.../_Lit/pdfs --update-yaml
  UNPAYWALL_EMAIL=you@example.com python3 scripts/fetch_pdfs.py --target ./pdfs

Options:
  --target DIR     where to save PDFs (default: Lit/pdfs)
  --email ADDR     Unpaywall contact email (or env UNPAYWALL_EMAIL)
  --update-yaml    write pdf path + oa_status back into Lit/lit.yaml
  --dry-run        resolve availability, download nothing
  --limit N        only process the first N records (testing)
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import yaml

DB = "Lit/lit.yaml"
UA = "Cyber-AI-Autonomy-lit/1.0 (academic reference collection; contact via UNPAYWALL_EMAIL)"


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(), r.headers.get_content_type()


def doi_from_url(url):
    m = re.search(r"(10\.\d{4,9}/[^\s?#]+)", url)
    if m:
        return m.group(1).rstrip("/")
    m = re.search(r"nature\.com/articles/([^\s?#/]+)", url)
    if m:
        return "10.1038/" + m.group(1)
    return None


def unpaywall_locations(doi, email):
    """Return (list_of_candidate_pdf_urls, status)."""
    api = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={urllib.parse.quote(email)}"
    try:
        _, body, _ = get(api)
        data = json.loads(body)
    except Exception as e:
        return [], f"unpaywall error: {e}"
    if not data.get("is_oa"):
        return [], "no open-access copy (Unpaywall)"
    locs = data.get("oa_locations") or []
    urls = [L["url_for_pdf"] for L in locs if L.get("url_for_pdf")]
    urls += [L["url"] for L in locs if L.get("url")]
    return urls, "open access"


def publisher_pdf_candidates(doi):
    """Direct-PDF URL patterns for common open-access publishers."""
    c = []
    if doi.startswith("10.1038/"):        # Nature
        c.append(f"https://www.nature.com/articles/{doi.split('/', 1)[1]}.pdf")
    if doi.startswith("10.1007/"):        # Springer
        c.append(f"https://link.springer.com/content/pdf/{doi}.pdf")
    if doi.startswith("10.1145/"):        # ACM
        c.append(f"https://dl.acm.org/doi/pdf/{doi}")
    if doi.startswith("10.1186/"):        # BioMed Central
        c.append(f"https://doi.org/{doi}")
    return c


def resolve(rec, email):
    """Return (candidate_pdf_urls, oa_status)."""
    ax = (rec.get("citation") or {}).get("arxiv_id")
    if ax:
        return [f"https://arxiv.org/pdf/{ax}"], "arxiv"
    doi = doi_from_url(rec.get("url", ""))
    if not doi:
        return [], "no DOI (gray lit / web page) — manual"
    urls, status = unpaywall_locations(doi, email)
    urls = urls + publisher_pdf_candidates(doi)
    seen, deduped = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped, (status if deduped else "no open-access copy")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="Lit/pdfs")
    ap.add_argument("--email", default=os.environ.get("UNPAYWALL_EMAIL", "jtread0000@gmail.com"))
    ap.add_argument("--update-yaml", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--pdf-prefix", default="",
                    help="if set, write this as the pdf: path prefix in lit.yaml "
                         "(e.g. the Dropbox folder) instead of the local target dir")
    ap.add_argument("--force", action="store_true",
                    help="re-fetch even records that already have a pdf: set")
    args = ap.parse_args()

    records = yaml.safe_load(open(DB, encoding="utf-8")) or []
    if args.limit:
        records = records[: args.limit]
    if not args.dry_run:
        os.makedirs(args.target, exist_ok=True)

    got, manual, skipped = [], [], []
    for rec in records:
        rid = rec["id"]
        if not args.force and not args.dry_run and rec.get("pdf"):
            skipped.append(rid)
            print(f"  HAVE    {rid}: already fetched ({rec['pdf']})")
            continue
        candidates, status = resolve(rec, args.email)
        if not candidates:
            manual.append((rid, status, [rec.get("url", "")]))
            print(f"  MANUAL  {rid}: {status}")
            time.sleep(0.2)
            continue
        if args.dry_run:
            got.append((rid, status))
            print(f"  OA      {rid}: {status} ({len(candidates)} candidate url(s))")
            time.sleep(0.5)
            continue
        year = (rec.get("citation") or {}).get("year")
        fname = f"{year}-{rid}.pdf" if year else f"{rid}.pdf"
        dest = os.path.join(args.target, fname)
        saved = False
        for cand in candidates:
            try:
                st, data, ctype = get(cand)
            except Exception as e:
                print(f"          {rid}: {cand} -> {e}")
                continue
            if "pdf" in (ctype or "") or data[:5] == b"%PDF-":
                with open(dest, "wb") as f:
                    f.write(data)
                rec["pdf"] = f"{args.pdf_prefix.rstrip('/')}/{fname}" if args.pdf_prefix else dest
                rec["oa_status"] = status
                got.append((rid, status))
                print(f"  SAVED   {rid} ({len(data)//1024} KB) [{status}] -> {rec['pdf']}")
                saved = True
                break
            print(f"          {rid}: {cand} served {ctype}, not a PDF")
            time.sleep(0.5)
        if not saved:
            manual.append((rid, "no candidate served a PDF", candidates + [rec.get("url", "")]))
            print(f"  MANUAL  {rid}: tried {len(candidates)} url(s), none returned a PDF")
        time.sleep(1.0)   # be polite

    if args.update_yaml and not args.dry_run:
        header = ("# Literature database for the Cyber-AI Autonomy study.\n"
                  "# Schema and workflow: see Lit/README.md. Regenerate views: python3 scripts/lit.py\n\n")
        with open(DB, "w", encoding="utf-8") as f:
            f.write(header)
            yaml.safe_dump(records, f, sort_keys=False, allow_unicode=True, width=100)

    print(f"\nFetched: {len(got)}   Already had: {len(skipped)}   "
          f"Manual (library/browser): {len(manual)}   of {len(records)}")
    if manual:
        print("\nTo fetch by hand (in your browser, via your library if paywalled):")
        for rid, why, urls in manual:
            print(f"  - {rid}: {why}")
            for u in (urls if isinstance(urls, list) else [urls]):
                if u:
                    print(f"      {u}")


if __name__ == "__main__":
    main()
