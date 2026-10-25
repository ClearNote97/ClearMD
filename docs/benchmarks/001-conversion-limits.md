# Benchmark 001 — Conversion limits

> T07 of feature 001. Raw data: [`001-results.json`](./001-results.json). Script:
> [`tests/benchmark/run_benchmark.py`](../../tests/benchmark/run_benchmark.py). Date: 2026-10-25.

## What was measured

For each format and size: the conversion time and the peak memory of markitdown 0.1.9, each run in a **fresh
spawn process** (like the worker of ADR-0015). Documents are generated pseudo-random prose with a fixed seed,
which compresses like real text (about 3–4:1). The parent stopped any run above **2 GiB**: this machine had
only ~4 GB free, shared with other containers.

**Machine:** WSL 2 on Windows, 16 CPUs, 15.5 GiB RAM, Python 3.14.5, inside the dev container.

## Results

| Format | File | Time | Peak memory | Speed | Notes |
|---|---|---|---|---|---|
| txt | 100 MiB | 2.4 s | 554 MiB | 41 MiB/s | |
| ipynb | 54 MiB | 1.4 s | 362 MiB | 40 MiB/s | |
| csv | 100 MiB | 14.7 s | 1,534 MiB | 6.8 MiB/s | memory ≈ 14× the file |
| html | 50 MiB | 9.7 s | 515 MiB | 5.2 MiB/s | |
| epub | 50 MiB | 20.9 s | 613 MiB | 2.4 MiB/s | |
| docx (text) | 50 MiB | 94 s | 1,980 MiB | 0.53 MiB/s | 155 MiB of XML inside |
| docx (photos) | 100 MiB | 1.3 s | 807 MiB | 76 MiB/s | images are not processed |
| pptx | 5 MiB | 12.9 s | 232 MiB | 0.41 MiB/s | |
| xlsx | 10 MiB | 65 s | 1,291 MiB | 0.15 MiB/s | 50 MiB stopped above 2 GiB |
| **pdf** | **20 MiB (~6,000 pages)** | **625 s** | 335 MiB | **~10 pages/s** | text-only pages |

**Worker start-up** (Python + markitdown + magika model): **0.7 s**, 161 MiB resident.
**A second magika model:** no measurable memory (within noise): keeping a separate instance for content
detection costs nothing.

**ZIP ratios of realistic documents:** whole file 1.0–4.7 (uncompressed / file size); the zip-bomb fixture is
~340. Single entries reach 43:1 (pptx template XML), so a per-entry rule would block legitimate files.

## Conclusions

1. **PDF is the time bottleneck** (~31 s per MiB of text pages, ~10 pages/s). The 10-minute limit fits about
   6,000 text pages: a 300-page thesis takes ~30 s, a 1,000-page book under 2 minutes.
2. **xlsx is the memory bottleneck** (~115 MiB of RAM per MiB of file). With the 4 GiB worker limit, an xlsx
   above ~30 MiB fails with `out_of_memory`. Every other format stays far below the limit at 50–100 MiB.
3. **The cost of a file is now its estimated time:** `size × seconds per MiB` (`schemas/limits.py`). For
   ZIP-based formats the size is the uncompressed **text** parts — counting images would make a docx of photos
   look 50× slower than it is. The queue order (ADR-0015) and the time-left estimate use this cost.
4. **The ratio rule applies to the whole file** (uncompressed total / file size > 100), never per entry.
5. **Unchanged:** 250 MiB per file, 1 GiB uncompressed, 4 GiB worker memory (half the RAM when smaller).

| Speed used (`SECONDS_PER_MIB`) | pdf | xlsx | pptx | docx | html | csv | epub | ipynb | txt |
|---|---|---|---|---|---|---|---|---|---|
| seconds per MiB | 31 | 1.5 | 1.2 | 0.6 | 0.2 | 0.15 | 0.15 | 0.03 | 0.03 |

## Caveats

- **Synthetic documents.** Real PDFs compress their text streams (more text per MiB) and carry tables and
  columns that pdfminer analyzes character by character: expect them slower per MiB. The time-left estimate
  corrects itself with the measured speed of each batch; real documents should be checked on the author's
  Windows machine.
- **Memory above 2 GiB was not measured** on this machine; the xlsx limit is an extrapolation.
- One machine, one run per size; numbers are orders of magnitude, not guarantees.

## Reproduce

```bash
uv run python tests/benchmark/run_benchmark.py --out docs/benchmarks/001-results.json
# options: --memory-cap-mib 2048 --timeout 900 --slow-after 300 --only pdf xlsx
```
