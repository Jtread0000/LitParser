---
name: litparser
description: >-
  Build and maintain a citation-honest literature database from publicly
  available sources (open-access PDFs via arXiv/Unpaywall) and your own stored
  PDFs, converting each to Markdown for cheap reading and verification. One YAML
  file is the source of truth; human-readable views (a status table, an APA
  reference list, a reading list) are generated from it, and a validator refuses
  to mark a source "cited" without a verified citation. Use when a user wants a
  tracked, verifiable set of references behind a paper, review, memo, or report.
  Triggers: "build a lit database", "track my references", "fetch these papers",
  "convert PDFs to markdown", "generate a reference list / bibliography".
---

# LitParser

A **YAML-as-database** for literature. `Lit/lit.yaml` is the source of truth;
`scripts/lit.py` generates the views and validates that nothing is cited without a
verified citation. Two ingest paths — open-access fetch and your own stored PDFs —
plus a PDF→Markdown step so every source is cheap to read and to verify against.

## When to use
- The user wants a **tracked, verifiable** set of sources behind a document.
- They have open-access papers to pull and/or personal PDFs already stored.
- They want a generated **reference list** and a **status table** (what's cited, where,
  and whether the citation is confirmed).

## Files
| Path | Role |
| --- | --- |
| `Lit/lit.yaml` | **Source of truth** — one record per source. |
| `scripts/lit.py` | Validate + generate `references-table.md`, `references.md`, `reading-list.md`. |
| `scripts/fetch_pdfs.py` | Fetch legal open-access PDFs (arXiv + Unpaywall) → Dropbox. |
| `scripts/pdf_to_md.py` | Convert each PDF → `Lit/md/<id>.md` (+ a source-PDF link block). |
| `scripts/add_pdf_links.py` | Backfill the source-PDF link into existing Markdown. |
| `scripts/seed_lit_from_md.py` | Seed `lit.yaml` from an existing annotated references Markdown. |
| `scripts/dropbox_*.py` | Dropbox helpers (rename to `<year>-<id>.pdf`, upload). |
| `.github/workflows/fetch-pdfs.yml` | Fetch → convert → regenerate → commit. |
| `docs/method.md` | The full method + schema. |
| `docs/gitdoc-tie-in.md` | Optional integration with the GitDoc writing skill. |

## Drive it
1. Add records to `Lit/lit.yaml` (or `seed_lit_from_md.py` from an existing list).
2. For open-access sources, run `fetch_pdfs.py`; for sources you already have, set
   the record's `pdf` to its Dropbox path.
3. `pdf_to_md.py` converts each to `Lit/md/<id>.md`; `add_pdf_links.py` adds the
   source link.
4. When you cite a source: `used: true`, fill the verified `apa`,
   `citation_status: verified`, note `where_used`.
5. `python3 scripts/lit.py` regenerates the views. `--check` validates only.

## Setup
`pip install -r requirements.txt`; for fetch/convert set the Dropbox secrets +
`DROPBOX_DEST_DIR` (see `docs/method.md`). Legal note: open-access retrieval only —
never library proxies or paywalled full text.

## Optional: GitDoc
Feeds the [GitDoc](https://github.com/Jtread0000/GitDoc) writing skill — citations
map to record ids so references and analysis are verifiable in one hop. See
`docs/gitdoc-tie-in.md`.
