Read ~/Documents/JT-agents/litparser/CLAUDE.md — that IS your identity.

This file is a thin pointer. Your full identity, tone, working scope, task
shapes, and mission live in the JT-agents monorepo, not here. This repo
(`~/PhD/litparser/`) is the *product*: JT's published, MIT-licensed LitParser
toolkit — a citation-honest literature database from a single YAML source of
truth — plus its new bridge that digests readings into Solomon.

**Respect the existing toolkit.** LitParser is vendored by other projects
(e.g. Cyber-AI_Autonomy). Its `README.md`, `SKILL.md`, `LICENSE`, `Lit/`,
`scripts/`, and `docs/` are the real tool — preserve them. Your PhD-stack
additions (the Solomon bridge) must not add hard deps on PhD-stack internals.
The digest-to-Solomon function is a *bridge, not a rewrite*.

## Boot order (every session)

1. `git -C ~/Documents/JT-agents pull origin main` — identity + PHRONESIS + contracts
2. `git -C ~/PhD/litparser pull origin main` — this repo
3. `Read ~/Documents/JT-agents/PHRONESIS.md` — universal stances
4. `Read ~/Documents/JT-agents/litparser/CLAUDE.md` — your identity (the real one)
5. `Read ~/Documents/JT-agents/litparser/memory/MEMORY.md` — your persistent memory
6. `Read ~/PhD/solomon/SOLOMON_CONTRACT.md` — the target for digested output
7. `Read ~/PhD/litparser/README.md` — LitParser's own model (respect it)
8. `Read ~/PhD/bus/inbox/litparser.jsonl` — tail for dispatched tasks
9. `Read ~/PhD/bus/broadcast.jsonl` — check for urgent broadcasts
10. See `COORDINATION.md` in this repo for how you talk on the bus.

## What lives here (yours to extend, not rewrite)

`Lit/lit.yaml` (source of truth), `Lit/md/<id>.md` (PDF→MD), `scripts/*.py`
(validator, fetchers, converters), `scripts/solomon_bridge.py` (**new** —
writes digested sources into Solomon via the bus), the reference views, and
`.github/workflows/`. You do NOT write to `~/PhD/solomon/vault/` — you dispatch
`source` entities to Solomon-worker's inbox; Solomon-worker commits them.
Legal-only fetch (arXiv, Unpaywall) — never a paywall bypass.
