# Benchmark 002 — The `.tex` converter

> T10 of feature 002. Raw data: [`002-results.json`](./002-results.json). Script:
> [`tests/benchmark/run_benchmark.py`](../../tests/benchmark/run_benchmark.py) (`--only tex tex_macros`).
> Date: 2026-10-25.

## What was measured

ClearMD's own converter (`TexConverter`: read, includes, macros, rendering, the output guarantee of ADR-0023)
on generated LaTeX, each run in a **fresh spawn process** like the worker of ADR-0015, the parent stopping any
run above **2 GiB**. Two documents, pseudo-random prose with a fixed seed, built only from the supported subset
(a smoke test checks that they convert without a single note, so everything measured is real work):

- **`tex`** — sections, paragraphs with bold/italic/code/citations/inline math/accents, footnotes, lists,
  equations, tables and quotes.
- **`tex_macros`** — the same, plus seven author macros (`\R`, `\norm{…}`, `\pair[…]{…}`,
  `\DeclareMathOperator`, `\def`…) used about 13 times per KiB, nested: denser than a real thesis.

**Machine:** WSL 2 on Windows, 16 CPUs, 15.5 GiB RAM, Python 3.14.5, inside the dev container, nothing else
running (an earlier run shared the container with a verification agent: within 5%).

## Results

| Document | File | Time | Speed | Peak memory | Memory per MiB |
|---|---|---|---|---|---|
| tex | 1 MiB | 3.1 s | 3.1 s/MiB | 66 MiB | 37 |
| tex | 5 MiB | 18.0 s | 3.6 s/MiB | 230 MiB | 40 |
| tex | 10 MiB | 43.0 s | 4.3 s/MiB | 432 MiB | 40 |
| tex | 25 MiB | 181 s | 7.3 s/MiB | 1,042 MiB | 41 |
| tex_macros | 1 MiB | 7.6 s | 7.6 s/MiB | 125 MiB | 96 |
| tex_macros | 5 MiB | 40.8 s | 8.2 s/MiB | 467 MiB | 88 |
| tex_macros | 10 MiB | 94.7 s | 9.5 s/MiB | 907 MiB | 88 |
| tex_macros | 25 MiB | — | — | over the 2 GiB cap | — |

## Conclusions

1. **A thesis converts in seconds.** A 300-page thesis is about 1 MiB of LaTeX: 3 s, or 8 s with heavy macro use.
2. **pylatexenc reads character by character, and slower per character in a longer text** (each token costs
   2.6 µs in a 2 MiB document, 3.5 µs in an 8 MiB one: work proportional to the whole text inside its
   tokenizer). Garbage collection is not the cause (disabling it changed nothing and doubled the memory). It
   stays within the limits: 25 MiB in 3 minutes, under the 10-minute limit per file (ADR-0015).
3. **Memory is about 40 MiB per MiB, twice that with macros** (pylatexenc keeps a node per token). With the
   4 GiB worker, a `.tex` above about 43 MiB is planned as "too much memory" and skipped with its reason —
   LaTeX sources that large are exceptional.
4. **Values used** (`schemas/limits.py`): `SECONDS_PER_MIB[TEX] = 7.5` (the largest measured, plain) and
   `MEMORY_PER_MIB[TEX] = 90` (the macro document from 5 MiB, where per-MiB costs dominate). A test
   (acceptance AC-22) ties both to `002-results.json`.
5. **The macro document reaches the expansion limit** (10,000, or 10 per KiB: ADR-0022) at every size: it uses
   about 13 expansions per KiB. Its uses past the limit stay as written, with the note. Whether 10 per KiB is
   enough for real theses is an open question for the author's documents.

## Caveats

- **Synthetic documents**, one machine, one run per size: orders of magnitude, not guarantees. Real theses
  should be checked on the author's Windows machine.
- The speed in the time-left estimate corrects itself with the measured speed of each batch (feature 001).
