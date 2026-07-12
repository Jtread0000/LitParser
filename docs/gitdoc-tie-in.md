# Optional tie-in with GitDoc

[GitDoc](https://github.com/Jtread0000/GitDoc) authors documents as Word tracked
changes synced to Dropbox. LitParser is its **evidence half**: the verified sources
your document cites. Wired together, every reference and analysis claim is checkable
in one hop.

## The seam: stable IDs

A citation in the GitDoc document maps to a LitParser record **`id`**. Because that
record carries the verified `apa` *and* the converted full text
(`Lit/md/<id>.md`), a reader — or a check — can go from a sentence → the record →
the exact passage it rests on.

## How they compose

1. **LitParser** builds and verifies the corpus: fetch/store PDFs → Markdown →
   `lit.yaml` with `used`, `where_used`, `apa`, `citation_status`.
2. **GitDoc** cites records by id and generates its bibliography from the
   `used: true` records (`Lit/references.md`) — so the reference list can't drift
   from the corpus.
3. A **verifier** (in the GitDoc project) can fail a build if a cited id is missing
   or unverified, or if a quoted span isn't found in that record's `Lit/md` text.

## Minimal wiring

Add LitParser to a GitDoc project as a submodule or sibling clone so the document
side can read the corpus:

```bash
git submodule add https://github.com/Jtread0000/LitParser lit
# cite [[REF: <id>]] in the document; generate references from lit/Lit/references.md
```

The tie-in is **optional** — LitParser is fully useful on its own as a literature
database; GitDoc just consumes what it produces.
