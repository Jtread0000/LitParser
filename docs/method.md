# The method

LitParser is a **YAML-as-database** for literature: one YAML file is the source of
truth, human-readable views are generated from it, and a validator keeps citations
honest. Around that core sit two ingest paths (open-access fetch + your own stored
PDFs) and a PDF→Markdown step so sources are cheap to read and verify against.

## Source of truth: `Lit/lit.yaml`

One record per source. Views are generated — never hand-edit them.

```yaml
- id: ai-induced-human-responsibility-aihr   # stable key (also the citation join key)
  status: to-review        # to-review | reviewing | reviewed
  used: false              # true once cited in your document
  source_type: PP          # PR peer-reviewed | PP preprint | GL gray lit
  load_bearing: true       # the ⭐ — carries the logic chain
  section: 3
  tags: [accountability, responsibility-gap]
  shortlist_rank: 1        # read-first order, or null
  title: ...
  url: ...
  summary: key insight (1-3 sentences)
  citation: {year: 2026, source: arXiv (preprint), arxiv_id: 2604.08866}
  apa: ""                  # verified APA 7th; REQUIRED before used: true
  citation_status: needs-verification   # -> verified once confirmed
  where_used: ""           # e.g. "Background ¶ (accountability)"
  pdf: ""                  # Dropbox path (from the fetcher, or your own stored file)
  md: ""                   # Lit/md/<id>.md — converted full text (git-tracked)
  notes: ""
```

## Generated views — `python3 scripts/lit.py`

| File | What |
| --- | --- |
| `Lit/references-table.md` | Status table — author · year · title · cited? · where · citation-in-place. |
| `Lit/references.md` | APA 7th list of `used: true` sources. |
| `Lit/reading-list.md` | Grouped by review status; load-bearing / read-first float up. |

`python3 scripts/lit.py --check` validates only. **The gate:** a record can't be
`used: true` without a filled, `verified` APA — so nothing reaches the document
uncited.

## Ingest 1 — publicly available resources (`scripts/fetch_pdfs.py`)

Resolves **legal open-access** copies only: arXiv direct PDFs, and Unpaywall for
DOIs. It **never** touches library proxies, logins, or paywalled full text —
paywalled items are listed for you to fetch by hand in your own browser. Fetched
PDFs are pushed to Dropbox `<DEST>/_Lit/pdfs/` and named **`<year>-<id>.pdf`**
(year-first, so the folder sorts chronologically). Re-runs skip records that
already have a `pdf`.

## Ingest 2 — personal documents you already stored

For a source you already have, point its record's `pdf` at the file's Dropbox
path. The converter treats it exactly like a fetched one — no re-download.
(`seed_lit_from_md.py` can also seed `lit.yaml` from an existing annotated
references Markdown to get started fast.)

## PDF → Markdown (`scripts/pdf_to_md.py`)

Each PDF is converted **once** to `Lit/md/<id>.md` (git-tracked, free/deterministic
via `pymupdf4llm`); reads and searches use that lean text instead of re-imaging the
PDF. Each Markdown opens with a **source-PDF block**: a clickable Dropbox "open this
file" link (built from the `pdf` path — no shared link is created), the path, and
the id. `scripts/add_pdf_links.py` backfills the block into existing files.

## Dropbox

The fetch/convert steps talk to the Dropbox HTTP API with an **offline refresh
token** (binary-safe, connector-independent). Set `DROPBOX_APP_KEY`,
`DROPBOX_APP_SECRET`, `DROPBOX_REFRESH_TOKEN` and `DROPBOX_DEST_DIR`. PDFs live in
Dropbox (not git); their Markdown is git-tracked.

## Naming & citations

- PDFs: **`<year>-<id>.pdf`** — apply to any future gathering so folders sort by year.
- Every record starts `citation_status: needs-verification`; verify against the
  actual paper before `used: true`. Style defaults to APA 7th.

## Provenance & reuse

This repo is the **canonical source** of the toolkit in `scripts/`. Projects that
build a literature database typically **vendor** these scripts (keep an in-repo
copy so the project runs standalone) rather than depend on this repo at runtime.
If you do that, record the LitParser commit you copied from — e.g. a
`scripts/VENDOR.txt` holding `LitParser@<commit-sha>` — so a later reader knows
where the canonical version lives and how to pull fixes forward.
