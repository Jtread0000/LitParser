#!/usr/bin/env python3
"""Seed a structured Lit/lit.yaml database from a plain Markdown references list.

Usage: python3 scripts/seed_lit_from_md.py [SRC.md] [OUT.yaml]
       (defaults: Lit/references-seed.md -> Lit/lit.yaml)

One-time seeding. After this, edit lit.yaml directly (or via Claude) and run
scripts/lit.py to regenerate the Markdown views.

NOTE: the section-tag map and shortlist heuristics below are example values
carried over from the project this tool was extracted from — adapt them (or
remove them) to fit your own reference list.
"""
import re
import sys
import yaml

SRC = sys.argv[1] if len(sys.argv) > 1 else "Lit/references-seed.md"
OUT = sys.argv[2] if len(sys.argv) > 2 else "Lit/lit.yaml"

SECTION_TAGS = {
    "0": ["method", "expert-elicitation"],
    "1": ["delegation"],
    "2": ["trust", "sentiment"],
    "3": ["accountability", "responsibility-gap"],
}
TYPE_MAP = {"PR": "PR", "PP": "PP", "GL": "GL"}

STOP = {"the", "a", "an", "of", "for", "and", "in", "to", "on", "with", "from",
        "how", "what", "is", "as", "at", "case", "towards", "toward"}


def slugify(title):
    words = re.findall(r"[A-Za-z0-9]+", title.lower())
    keep = [w for w in words if w not in STOP][:5]
    return "-".join(keep) or "ref"


def parse():
    text = open(SRC, encoding="utf-8").read()
    lines = text.splitlines()
    records = []
    section = section_title = None
    in_numbered = False
    for line in lines:
        m = re.match(r"^##\s+(\d+)\.\s+(.*)$", line)
        if m:
            section = m.group(1)
            section_title = m.group(2).split("(")[0].strip()
            in_numbered = True
            continue
        if line.startswith("## "):   # a non-numbered section (shortlist, one-liner)
            in_numbered = False
            continue
        if not in_numbered or not line.strip().startswith("- "):
            continue
        item = line.strip()[2:]
        load_bearing = item.startswith("⭐")
        tm = re.search(r"`\[(PR|PP|GL)\]`", item)
        source_type = TYPE_MAP.get(tm.group(1)) if tm else None
        title_m = re.search(r"\*\*(.+?)\*\*", item)
        if not title_m:
            continue
        title = title_m.group(1).strip()
        url_m = re.search(r"(https?://\S+)", item)
        url = url_m.group(1).rstrip(".") if url_m else ""
        # annotation: between the title and the url, minus a leading " — "
        after = item[title_m.end():]
        after = after.split(url, 1)[0] if url else after
        paren = re.search(r"^\s*\(([^)]*)\)", after)
        source_hint = paren.group(1).strip() if paren else None
        annotation = re.sub(r"^\s*\([^)]*\)", "", after).strip()
        annotation = annotation.lstrip("—-").strip().rstrip(".").strip()
        year_m = re.search(r"\b(19|20)\d{2}\b", (source_hint or "") + " " + item)
        year = int(year_m.group(0)) if year_m else None
        ax = re.search(r"arxiv\.org/(?:pdf|abs|html)/([\d.]+)", url)
        arxiv_id = ax.group(1).rstrip(".") if ax else None
        if year is None and arxiv_id and re.match(r"\d{4}\.", arxiv_id):
            year = 2000 + int(arxiv_id[:2])   # arXiv IDs are YYMM.NNNNN
        source = "arXiv (preprint)" if arxiv_id else (source_hint or "")
        records.append({
            "id": slugify(title),
            "status": "to-review",
            "used": False,
            "source_type": source_type,
            "load_bearing": load_bearing,
            "section": int(section),
            "section_title": section_title,
            "tags": list(SECTION_TAGS.get(section, [])),
            "shortlist_rank": None,
            "title": title,
            "url": url,
            "summary": annotation,
            "citation": {"year": year, "source": source, "arxiv_id": arxiv_id},
            "apa": "",
            "citation_status": "needs-verification",
            "where_used": "",
            "pdf": "",
            "notes": "",
        })
    # unique ids
    seen = {}
    for r in records:
        base = r["id"]
        if base in seen:
            seen[base] += 1
            r["id"] = f"{base}-{seen[base]}"
        else:
            seen[base] = 1
    # shortlist ranks (match by keyword against the Read-first list)
    shortlist = [
        (1, "AIHR"), (2, "knowledge and importance"), (3, "Human Factors"),
        (4, "Software-Defined Vehicles"), (5, "Augmented Intelligence Framework"),
    ]
    for rank, kw in shortlist:
        for r in records:
            if kw.lower() in r["title"].lower():
                r["shortlist_rank"] = rank
                break
    return records


def main():
    records = parse()
    header = ("# Literature database (source of truth).\n"
              "# Schema and workflow: see docs/method.md. Regenerate views: python3 scripts/lit.py\n"
              "# status: to-review | reviewing | reviewed   used: true once cited\n\n")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(records, f, sort_keys=False, allow_unicode=True, width=100)
    print(f"Wrote {OUT}: {len(records)} records")
    by = {}
    for r in records:
        by[r["section_title"]] = by.get(r["section_title"], 0) + 1
    for k, v in by.items():
        print(f"  §{k}: {v}")


if __name__ == "__main__":
    main()
