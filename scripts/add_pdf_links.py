#!/usr/bin/env python3
"""Prepend a source-PDF link block to each existing Lit/md/<id>.md.

Idempotent: files that already carry the marker are left alone. New conversions
get the block automatically (see scripts/pdf_to_md.py). Run:  python3 scripts/add_pdf_links.py
"""
import os

import yaml

from pdf_to_md import DB, MD_DIR, SRC_MARK, source_header


def main():
    records = yaml.safe_load(open(DB, encoding="utf-8")) or []
    updated = 0
    for rec in records:
        if not rec.get("pdf"):
            continue
        md_path = f"{MD_DIR}/{rec['id']}.md"
        if not os.path.exists(md_path):
            continue
        body = open(md_path, encoding="utf-8").read()
        if SRC_MARK in body[:400]:
            continue  # already has the link block
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(source_header(rec) + body)
        updated += 1
        print(f"  linked {rec['id']}.md")
    print(f"Added source-PDF link to {updated} markdown file(s).")


if __name__ == "__main__":
    main()
