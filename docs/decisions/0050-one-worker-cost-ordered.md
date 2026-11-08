# ADR-0050: One worker, cost-ordered: no second lane, no parallel workers (measured)

- **Status:** accepted
- **Date:** 2026-11-08
- **Refines:** ADR-0015 (the worker process and its cost-ordered queue).

## Context

ADR-0015 left open a second lane for heavy files, or several workers, "only if the benchmark
shows blocking". Feature 030 measured it.

## Measurement

Five small text files and a 400-page text PDF, in the dev container, on the real worker:

- each small file finished at 1.2 s (the worker's start-up);
- the PDF finished at 15.7 s (estimated 32 s).

Light files never wait for a heavy one: the plan puts the cheapest first.

## Decision

- **Keep one worker and the cost order.** No second lane, no parallel workers.
- **Why not parallel:**
  - each worker may use up to half the RAM (at most 4 GiB, ADR-0015), so two of them on an
    8 GB laptop risk swapping, which is slower;
  - PDF conversion is CPU-bound, and the user's other programs need cores too;
  - parallel progress, cancelling and time estimates are harder to show clearly.
- An acceptance test keeps the measured property: light files finish before a heavy one
  starts.
- **Revisit** if users report batches of many large PDFs. Then a second worker, gated on the
  machine's free memory, is the option to measure.

## Consequences

- **Gains:** the design stays simple, memory stays predictable, and the progress is clear.
- **Cost:** a batch of many large PDFs takes their sum. Split (023) and "Split the Large PDFs"
  (025) are the answer for one very large file.
