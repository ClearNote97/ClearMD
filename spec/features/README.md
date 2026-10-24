# spec/features — Levels 2–4: one folder per feature

Each feature lives in a numbered folder (`001_batch-conversion-core-cli`, …) with three files:

- `spec.md` — **what** it does and what must be true (acceptance criteria with ids, `AC-NN`).
- `plan.md` — **how** it is built (architecture, contracts, testing strategy).
- `tasks.md` — executable **steps**, in order.

To start a new feature, copy the structure of the most recent one. Every acceptance criterion gets an
acceptance test named after its id.
