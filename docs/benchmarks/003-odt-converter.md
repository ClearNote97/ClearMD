# Benchmark 003 — The `.odt` converter

> T09 of feature 003. Raw data: [`003-results.json`](./003-results.json). Script:
> [`tests/benchmark/run_benchmark.py`](../../tests/benchmark/run_benchmark.py) (`--only odt`).
> Date: 2026-10-25.

## What was measured

ClearMD's own converter (`OdtConverter`: the package check, the `pyexpat` tree with its limits, styles, the
text subset, a formula converted to LaTeX every seventh paragraph, the output guarantee) on generated
OpenDocument text, each run in a **fresh spawn process** like the worker of ADR-0015. The document is
pseudo-random prose with a fixed seed: headings, paragraphs with bold and italic spans, footnotes, lists, tables
and formulas; a smoke test checks it converts without a single note, so everything measured is real work.
Sizes are the size of `content.xml` — the text part, which is what the cost of a ZIP-based format counts
(feature 001) — about 4.3 times the file on disk.

**Machine:** WSL 2 on Windows, 16 CPUs, 15.5 GiB RAM, Python 3.14.5, inside the dev container, nothing else
running.

## Results

| `content.xml` | File | Time | Speed | Peak memory | Memory per MiB |
|---|---|---|---|---|---|
| 1 MiB | 0.24 MiB | 0.33 s | 0.33 s/MiB | 40 MiB | 14.1 |
| 5 MiB | 1.17 MiB | 1.69 s | 0.34 s/MiB | 100 MiB | 14.5 |
| 10 MiB | 2.34 MiB | 3.29 s | 0.33 s/MiB | 174 MiB | 14.7 |
| 25 MiB | 5.86 MiB | 8.26 s | 0.33 s/MiB | 398 MiB | 14.9 |

Measured again on 2026-10-26, after the three rounds of review fixes (the output guarantee, the growth
budget charging every write, the exact emphasis check): about 10% slower than the first run (0.30 s/MiB), still
within the values used.

## Conclusions

1. **Linear and fast.** About 0.33 s per MiB of text whatever the size: a 300-page report (about 1–2 MiB of
   `content.xml`) converts in under a second. pyexpat does the parsing in C; the tree and the rendering are
   linear by construction (no recursion, no quadratic joins).
2. **Memory is about 15 MiB per MiB of `content.xml`** (the element tree of a whole document). With the
   4 GiB worker, a document with more than about 270 MiB of text would be skipped as "too much memory" — the
   1 GiB uncompressed limit of feature 001 stays far above any real document.
3. **Values used** (`schemas/limits.py`): `SECONDS_PER_MIB[ODT] = 0.35` and `MEMORY_PER_MIB[ODT] = 15`. A test
   (acceptance AC-20) ties both to `003-results.json`.
4. **The benchmark changed a limit:** the first run reached the cap of 2,000 formula objects at 10 MiB,
   because one object was referenced thousands of times. Objects are now read once each and cached; the cap
   counts distinct objects and is the ZIP entry limit (50,000), so a reference can never multiply the work
   (ADR-0024).

## Caveats

- **Generated documents**, one machine, one run per size; real files exported by LibreOffice were checked for
  correctness, not timed.
