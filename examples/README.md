# examples/

Scratch space for worked examples — a sample references list to seed from, a
trial `lit.yaml`, or exported views you want to keep around while learning the
tool. Nothing here is read by the scripts.

The canonical starting point ships in the repo already: the two example records
in [`../Lit/lit.yaml`](../Lit/lit.yaml). Copy one, edit it, and run
`python3 scripts/lit.py` to see the generated views update. When you seed from a
Markdown references list, `scripts/seed_lit_from_md.py` reads
`Lit/references-seed.md` by default (override with a path argument).
