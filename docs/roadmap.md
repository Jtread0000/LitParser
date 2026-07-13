# Roadmap / notes

Enhancements to the LitParser template.

## Generated "Processed files" list in the repo README  ✅ done

**Implemented** in `scripts/lit.py` (`write_readme_processed`). The section below
records the original design; it now works as specified.

**Goal:** when LitParser is cloned as a template and then populated, the **new
repo's `README.md`** should carry an auto-generated list of the files that have
been processed, each with a clickable link to its **source PDF** — the same
presentation the originating project (`Cyber-AI_Autonomy`) already produces.

**What "just like the prototype" means.** In that project every converted source
lands at `Lit/md/<id>.md` and opens with a source-link block, e.g.:

```markdown
<!-- source-pdf -->
> **Source PDF:** [2026-agentic-ai-cybersecurity-meta-cognitive.pdf](https://www.dropbox.com/…?preview=…)
> **Dropbox path:** `/…/pdfs/2026-agentic-ai-cybersecurity-meta-cognitive.pdf`
> **Record:** `agentic-ai-cybersecurity-meta-cognitive` — see `Lit/lit.yaml`
```

That link is written by `scripts/add_pdf_links.py` after `pdf_to_md.py` converts
the PDF. The roadmap item is to **roll those per-source links up into the README**
so a reader sees, at the repo's landing page, every processed source and a direct
path to its PDF — rather than having to open each `Lit/md/` file.

**Proposed shape.** `scripts/lit.py` already regenerates the views
(`reading-list.md`, `references.md`, `references-table.md`) from `Lit/lit.yaml`.
Extend it to also emit a **Processed files** section — one row per source that has
both a `pdf` and a converted `md`:

| Source (id) | Title | Source PDF | Markdown |
| --- | --- | --- | --- |
| `agentic-ai-…` | Agentic AI for Cybersecurity … | [PDF](…) | [`Lit/md/agentic-ai-….md`](…) |

Render it between two markers in the README so regeneration is idempotent and
never clobbers hand-written prose:

```markdown
<!-- lit:processed-files:start -->
… generated table …
<!-- lit:processed-files:end -->
```

If the markers are absent (e.g. the untouched template README) the generator is a
no-op, so this stays invisible until a repo is actually populated.

**Acceptance:** after `python3 scripts/lit.py` on a populated clone, `README.md`
lists every processed source with a working link to its source PDF, matching the
link style used in `Lit/md/<id>.md`.

## Known limitations

- **`scripts/seed_lit_from_md.py` carries example heuristics.** The section-tag
  map and the shortlist keyword ranks are values carried over from the project
  LitParser was extracted from. They run harmlessly but won't be meaningful for
  your reference list — adapt or delete them. The seeder reads
  `Lit/references-seed.md` by default (override with a path argument). A fully
  generic seeder (format-agnostic, no baked-in tags) is a possible future
  improvement.
