# tests/benchmark — Conversion limits benchmark (T07)

`run_benchmark.py` measures, per format and size, the conversion time and the peak memory of markitdown in a
fresh *spawn* process (like the worker, ADR-0015), plus the worker start-up and the memory of a second magika
model. It is a script, not part of the default test run, because it takes minutes:

```bash
uv run python tests/benchmark/run_benchmark.py --out docs/benchmarks/001-results.json
```

`test_run_benchmark.py` runs every generator and one measurement at tiny sizes inside the normal suite, so the
script cannot rot. Results and conclusions: `docs/benchmarks/001-conversion-limits.md`.
