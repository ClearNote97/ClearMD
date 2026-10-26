# docs/benchmarks — Measured performance and limits

Each benchmark has a write-up (`NNN-*.md`: what was measured, results, conclusions) and its raw data
(`NNN-results.json`), produced by a script under `tests/benchmark/` that anyone can rerun.

| Benchmark | About |
|---|---|
| [`001-conversion-limits.md`](./001-conversion-limits.md) | Time and memory per format and size; sets the limits and speeds of ADR-0015. |
| [`002-tex-converter.md`](./002-tex-converter.md) | Time and memory of ClearMD's own `.tex` converter, with and without the author's macros. |
| [`003-odt-converter.md`](./003-odt-converter.md) | Time and memory of ClearMD's own `.odt` converter, formulas included. |
