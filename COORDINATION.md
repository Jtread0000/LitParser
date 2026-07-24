# COORDINATION.md — how LitParser-worker talks on the bus

The full protocol is `~/Documents/JT-agents/PROTOCOL.md`. This is the
worker-facing summary. When the two disagree, PROTOCOL wins. This file is a
PhD-stack overlay on a portable toolkit — it does not change LitParser's
public behavior for external users.

## Your channels

| File | Direction | You |
|---|---|---|
| `~/PhD/bus/inbox/litparser.jsonl` | PhDArc → you | tail (read) |
| `~/PhD/bus/outbox/litparser.jsonl` | you → PhDArc | append (write) |
| `~/PhD/bus/status/litparser.json` | you → readers | rewrite on state change |
| `~/PhD/bus/broadcast.jsonl` | PhDArc → all | tail every session |

## The coordinator rule

Your dispatcher is **PhDArc**. State-changing coordination routes through
PhDArc — you never edit another worker's repo or the umbrella docs. Critically:
any change that would touch LitParser's **public README/SKILL/docs** is a
ripple to external users (Cyber-AI_Autonomy) — raise it as `task.blocked`
(priority `block`) so JT decides, never edit unilaterally.

You never escalate to JT directly. Raise a `task.blocked` outbox event; PhDArc
decides whether it reaches JT — e.g. a citation can't be verified (no DOI /
publisher record / ISBN), a PDF is paywalled (halt, do not proxy), or
Solomon-worker rejects a `source` entity (contract mismatch).

## The Solomon bridge (digest → Solomon)

`scripts/solomon_bridge.py` is the handoff. Per LitParser YAML record:
1. Read the record + its converted MD.
2. Construct a Solomon `source` entity conforming to `SOLOMON_CONTRACT.md`.
3. Dispatch a `solomon.write.source` task to Solomon-worker's inbox
   (`~/PhD/bus/inbox/solomon.jsonl`).
4. Await confirmation in Solomon-worker's outbox.
5. Write `solomon_id: <returned>` back into the LitParser YAML — bidirectional.

You never `cp` into `~/PhD/solomon/vault/`. One owner per substrate: the vault
is Solomon-worker's.

## Task lifecycle (inbox → outbox)

1. Read the task (`kind: litparser.<verb>.<noun>`, e.g. `litparser.digest.batch`).
2. Ack: append `{"kind":"task.started","task_id":"…"}` to outbox.
3. Work on a feature branch → open PR (`gh pr create`).
4. Append `{"kind":"task.pr_opened","pr_url":"…","notes":"…"}`.
5. On merge: append `{"kind":"task.done","task_id":"…"}`.

Rewrite `status/litparser.json` on every material transition.

## Stateless reads (direct, no PhDArc hop)

Other workers query you directly — e.g. LitDrafter sends `litparser.query.by_id`
with `reply_to: "litdrafter"`; you reply with a `query.response` addressed
`to: "litdrafter"` in your outbox. Reads don't change shared state, so no
PhDArc involvement.

## Message shapes

See `~/Documents/JT-agents/PROTOCOL.md §Bus message schemas`.
