#!/usr/bin/env python3
"""Generate the human-readable views from Lit/lit.yaml (the source of truth).

  python3 scripts/lit.py            # validate + regenerate views
  python3 scripts/lit.py --check    # validate only (nonzero exit on problems)

Outputs:
  Lit/reading-list.md   grouped by status, for scanning what to read next
  Lit/references.md     only used==true, APA-formatted, for the paper's reference list
"""
import posixpath
import re
import sys
import urllib.parse

import yaml

DB = "Lit/lit.yaml"
READING = "Lit/reading-list.md"
REFERENCES = "Lit/references.md"
TABLE = "Lit/references-table.md"
README = "README.md"
PROC_START = "<!-- lit:processed-files:start -->"
PROC_END = "<!-- lit:processed-files:end -->"

STATUSES = ["to-review", "reviewing", "reviewed"]
TYPE_LABEL = {"PR": "peer-reviewed", "PP": "preprint", "GL": "gray lit"}


def load():
    return yaml.safe_load(open(DB, encoding="utf-8")) or []


def validate(records):
    problems = []
    ids = set()
    for i, r in enumerate(records):
        rid = r.get("id", f"<record {i}>")
        if not r.get("id"):
            problems.append(f"record {i}: missing id")
        if rid in ids:
            problems.append(f"{rid}: duplicate id")
        ids.add(rid)
        if r.get("status") not in STATUSES:
            problems.append(f"{rid}: status must be one of {STATUSES}")
        if not isinstance(r.get("used"), bool):
            problems.append(f"{rid}: used must be true/false")
        if r.get("used") and not r.get("apa"):
            problems.append(f"{rid}: used=true but apa is empty (add the citation before citing)")
        if r.get("used") and r.get("citation_status") == "needs-verification":
            problems.append(f"{rid}: used=true but citation_status is still needs-verification")
    return problems


def badge(r):
    bits = [TYPE_LABEL.get(r.get("source_type"), r.get("source_type") or "?")]
    if r.get("load_bearing"):
        bits.append("load-bearing")
    if r.get("shortlist_rank"):
        bits.append(f"read-first #{r['shortlist_rank']}")
    return ", ".join(bits)


def write_reading_list(records):
    lines = ["# Reading list", "",
             "Generated from `lit.yaml` by `scripts/lit.py` — do not edit by hand.", ""]
    total = len(records)
    used = sum(1 for r in records if r.get("used"))
    counts = {s: sum(1 for r in records if r.get("status") == s) for s in STATUSES}
    lines.append(f"**{total} sources** — "
                 + ", ".join(f"{counts[s]} {s}" for s in STATUSES)
                 + f"; {used} cited.")
    lines.append("")
    for s in STATUSES:
        group = [r for r in records if r.get("status") == s]
        if not group:
            continue
        # load-bearing and read-first float up
        group.sort(key=lambda r: (r.get("shortlist_rank") or 99,
                                   not r.get("load_bearing"), r.get("id")))
        lines.append(f"## {s} ({len(group)})")
        lines.append("")
        for r in group:
            cite = f" ({r['citation']['year']})" if r.get("citation", {}).get("year") else ""
            mark = "✅" if r.get("used") else "•"
            lines.append(f"- {mark} **{r['title']}**{cite} — _{badge(r)}_")
            if r.get("summary"):
                lines.append(f"  - {r['summary']}")
            meta = []
            if r.get("tags"):
                meta.append("tags: " + ", ".join(r["tags"]))
            if r.get("url"):
                meta.append(f"[link]({r['url']})")
            if r.get("pdf"):
                meta.append(f"pdf: {r['pdf']}")
            if meta:
                lines.append(f"  - {' · '.join(meta)}")
            lines.append(f"  - `id: {r['id']}`")
        lines.append("")
    open(READING, "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")


def write_references(records):
    used = [r for r in records if r.get("used")]
    lines = ["# References (cited sources)", "",
             "Generated from `lit.yaml` (records with `used: true`) by `scripts/lit.py`. "
             "APA 7th. Paste into your document's references section.", ""]
    if not used:
        lines.append("_No sources marked `used: true` yet._")
    else:
        for r in sorted(used, key=lambda r: (r.get("apa") or r.get("title") or "").lower()):
            lines.append(f"- {r.get('apa') or '[[CITE: APA for ' + r['id'] + ']]'}")
            if r.get("where_used"):
                lines.append(f"  - used in: {r['where_used']}")
    open(REFERENCES, "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")


def first_author(r):
    """Short author label from the APA string (e.g. 'Nyilasy et al.', 'Kleve &
    Barons', 'Malatji'). Falls back to '—' when no citation is captured yet."""
    apa = r.get("apa") or ""
    if not apa:
        return "—"
    authors = apa.split("(")[0].strip()
    n = len(re.findall(r"[^\s,]+,\s+[A-Z]\.", authors)) or 1  # count "Surname, X." groups
    s1 = authors.split(",")[0].strip()                        # first surname (allows spaces)
    if n == 1:
        return s1
    if n == 2:
        s2 = authors.split("&")[-1].strip().split(",")[0].strip()
        return f"{s1} & {s2}"
    return f"{s1} et al."


def cite_state(r):
    if not r.get("used"):
        return "—"
    if r.get("citation_status") == "verified" and r.get("apa"):
        return "✅ in place"
    return "⚠ unverified"


def _row(r):
    year = (r.get("citation") or {}).get("year") or "—"
    title = (r.get("title") or "").replace("|", "\\|")
    inpaper = "✅ yes" if r.get("used") else "—"
    where = (r.get("where_used") or "—").replace("|", "\\|") if r.get("used") else "—"
    return f"| {first_author(r)} | {year} | {title} | {inpaper} | {where} | {cite_state(r)} |"


def write_table(records):
    used = [r for r in records if r.get("used")]
    unused = [r for r in records if not r.get("used")]
    head = "| Author | Year | Title | In paper? | Where used | Citation |\n" \
           "| --- | --- | --- | --- | --- | --- |"
    lines = ["# References — status table", "",
             "Generated from `lit.yaml` by `scripts/lit.py` — do not edit by hand. "
             "The database schema and workflow (how to build one) live in `docs/method.md`; "
             "this view is your sources and their citation status.", "",
             f"**{len(records)} sources** — {len(used)} cited, {len(unused)} not yet cited.", ""]
    lines += [f"## Cited ({len(used)})", ""]
    if used:
        lines.append(head)
        for r in sorted(used, key=lambda r: (r.get("where_used") or "", first_author(r).lower())):
            lines.append(_row(r))
    else:
        lines.append("_None cited yet._")
    lines += ["", f"## Not yet cited ({len(unused)})", ""]
    if unused:
        lines.append(head)
        for r in sorted(unused, key=lambda r: (-((r.get("citation") or {}).get("year") or 0),
                                               (r.get("title") or "").lower())):
            lines.append(_row(r))
    else:
        lines.append("_All sources are cited._")
    open(TABLE, "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")


def _pdf_link(pdf):
    """Dropbox "open this file" web link, identical to the block pdf_to_md.py
    writes into each Lit/md/<id>.md (no shared link is created)."""
    folder = posixpath.dirname(pdf)
    fn = posixpath.basename(pdf)
    url = f"https://www.dropbox.com/home{folder}?preview={urllib.parse.quote(fn)}"
    return fn, url


def write_readme_processed(records):
    """Refresh the generated 'Processed files' table in README.md, in place,
    between the PROC_START/PROC_END markers. No-op (returns False) when the repo
    has no README or the markers aren't present — so the untouched template and
    any hand-written README are left completely alone."""
    try:
        text = open(README, encoding="utf-8").read()
    except FileNotFoundError:
        return False
    if PROC_START not in text or PROC_END not in text:
        return False

    done = [r for r in records if r.get("pdf") and r.get("md")]
    body = []
    if done:
        body.append("| Source | Title | Source PDF | Markdown |")
        body.append("| --- | --- | --- | --- |")
        for r in sorted(done, key=lambda r: (r.get("title") or r["id"]).lower()):
            title = (r.get("title") or "").replace("|", "\\|")
            fn, url = _pdf_link(r["pdf"])
            md = r["md"]
            body.append(f"| `{r['id']}` | {title} | [{fn}]({url}) | [`{md}`]({md}) |")
    else:
        body.append("_No processed sources yet — add PDFs and run the pipeline "
                    "(`pdf_to_md.py` → `add_pdf_links.py`), then `python3 scripts/lit.py`._")

    block = PROC_START + "\n" + "\n".join(body) + "\n" + PROC_END
    new = re.sub(re.escape(PROC_START) + r".*?" + re.escape(PROC_END),
                 lambda _m: block, text, count=1, flags=re.S)
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
    return True


def main():
    records = load()
    problems = validate(records)
    if problems:
        print("Validation problems:")
        for p in problems:
            print(f"  - {p}")
        if "--check" in sys.argv:
            sys.exit(1)
    elif "--check" in sys.argv:
        print(f"OK: {len(records)} records, no problems.")
        return
    write_reading_list(records)
    write_references(records)
    write_table(records)
    readme = write_readme_processed(records)
    used = sum(1 for r in records if r.get("used"))
    processed = sum(1 for r in records if r.get("pdf") and r.get("md"))
    print(f"Regenerated views: {len(records)} sources, {used} used. "
          f"Wrote {READING}, {REFERENCES}, {TABLE}.")
    if readme:
        print(f"Updated {README}: {processed} processed file(s) listed.")


if __name__ == "__main__":
    main()
