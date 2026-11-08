# Feature 030 — Measure the queue

## Goal

ADR-0015 left "a second lane for heavy files, or parallel workers" open, *only if blocking
shows*. This feature measures it on the real worker and records the decision (ADR-0050).

## Measurement (2026-11-08, dev container, the real worker)

A folder with five small text files and one 400-page text PDF (estimated 32 s):

| File | Finished at |
|---|---|
| small0.txt … small4.txt | 1.2 s each (the worker's start-up) |
| heavy.pdf | 15.7 s |

The queue already orders by estimated cost, so no light file waits for a heavy one.

## Acceptance criteria (what MUST be true)

- [x] **AC-01** In a batch with one heavy PDF and light files, every light file finishes before
  the heavy one starts (the real worker, measured by the batch's own events).
- [x] **AC-02** The decision is recorded: no second lane and no parallel workers (ADR-0050), with
  the measurement and the reasons.
