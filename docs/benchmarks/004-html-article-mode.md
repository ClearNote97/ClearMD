# Benchmark 004 — HTML article mode

> T06 of feature 004. Raw data: [`004-results.json`](./004-results.json). Script:
> [`tests/benchmark/run_benchmark.py`](../../tests/benchmark/run_benchmark.py) (`--only html_article`).
> Date: 2026-10-26.

## What was measured

The article strategy (`ArticleConverter`: trafilatura finds the article, ClearMD's limited XML reader reads it,
the renderer writes it through the shared output guarantee) on generated news pages: a menu, a cookie banner,
an aside and a footer around an article with every construct of the subset (headings, emphasis, links, nested
lists, quotes, tables, code, images). Each run is a **fresh spawn process** like the worker of ADR-0015. Sizes
are the size of the HTML file.

**Machine:** WSL 2 on Windows, 16 CPUs, 15.5 GiB RAM, Python 3.14.5, inside the dev container.

## Results

| HTML | Time | Speed | Peak memory | Memory per MiB |
|---|---|---|---|---|
| 1 MiB | 1.15 s | 1.15 s/MiB | 185 MiB | 41.9 |
| 5 MiB | 8.81 s | 1.76 s/MiB | 334 MiB | 38.2 |
| 10 MiB | 23.8 s | 2.38 s/MiB | 529 MiB | 38.4 |
| 25 MiB | 142 s | 5.68 s/MiB | 1100 MiB | 38.2 |

## Conclusions

1. **The first run changed the converter.** With trafilatura's XML output and its metadata, 25 MiB took 747 s,
   past the 600 s limit, growing with the square of the size. A profile showed that the extraction itself was
   not the cost: the date search (`htmldate`), the clean-up of trafilatura's XML output and a fingerprint for
   deduplication were. ClearMD uses none of them, so it now calls `bare_extraction` without metadata and reads the
   article's tree directly: 5 times faster at 25 MiB.
2. **Still faster than linear growth** inside trafilatura's extraction (about ×2.7 per doubling at large sizes),
   which ClearMD does not patch. Real saved pages are a few hundred KiB to a few MiB: well under a second to a
   few seconds. A hostile page large enough to run long is stopped by the worker's time limit, like any file.
3. **Values used** (`schemas/limits.py`): `ARTICLE_SECONDS_PER_MIB = 6.0` (the factor at 25 MiB, so smaller pages
   are over-estimated, never under) and `ARTICLE_MEMORY_PER_MIB = 42`. The plan uses them for HTML files planned
   with the article strategy; the full page keeps markitdown's factors (benchmark 001). A test (acceptance AC-11)
   ties both to `004-results.json`.
