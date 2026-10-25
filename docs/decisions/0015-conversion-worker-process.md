# ADR-0015: Conversions run in a worker process, with resource limits and a cost-ordered queue

- **Status:** accepted; values measured in `docs/benchmarks/001-conversion-limits.md` (cost = estimated seconds;
  ZIP sizes count text parts only; the ratio applies to the whole file)
- **Date:** 2026-10-25

## Context

ADR-0001 planned a synchronous core with a cancellation token checked between files. Reviewing it against
the real libraries showed three problems:

1. **A thread cannot be stopped.** A pathological PDF can keep pdfminer busy for minutes. In a GUI the
   conversion runs in a worker thread, and Python offers no way to kill a thread: the **Cancel** button of the
   UX contract would wait for the current file to finish.
2. **Input documents are untrusted** (ADR-0010). docx, pptx, xlsx and epub are ZIP archives: a 2 MB docx can
   expand to gigabytes (a *zip bomb*) and pass the 250 MiB file-size limit untouched. Native code
   (onnxruntime, pdfium) can also crash the whole process.
3. **markitdown runs magika on every file.** Verified in `markitdown/_markitdown.py` 0.1.9: `MarkItDown()`
   loads the magika model in its constructor and calls it on every conversion. Creating a converter per file
   would pay that load each time.

## Decision

### A persistent worker process

- Conversions run in **one child process** (`multiprocessing`, *spawn* start method on every OS). The parent
  sends one file at a time and receives the Markdown text back; the parent writes it (atomically).
- The worker **imports markitdown and magika once** and converts files one after another. The parent never
  imports them, so a GUI stays light.
- The parent kills the worker and starts a new one when:
  - the user **cancels** (the cancellation is immediate, not at the next file);
  - a file exceeds the **time limit**;
  - the worker exceeds the **memory limit**, measured with **`psutil`** (BSD; the only portable way to read a
    process's memory on Windows);
  - the worker **dies** on its own.
  The file is reported as failed with its own error code and the batch continues.
- In a PyInstaller executable this needs `multiprocessing.freeze_support()` at the entry point.

### Limits (initial values, fixed in v1, tuned by the benchmark)

| Limit | Value |
|---|---|
| File size | 250 MiB (ADR-0010) |
| Uncompressed size of a ZIP-based document | 1 GiB in total, compression ratio ≤ 100:1 |
| Time per file | 10 minutes |
| Worker memory | half of the machine's RAM, at most 4 GiB |

ZIP-based documents are checked **from their central directory, without decompressing anything**, while the
plan is built: a suspicious file is skipped before the user confirms.

### A queue ordered by estimated cost

With one worker the total time does not depend on the order, but the **perceived** wait does. Files are
processed from the cheapest to the most expensive (*shortest job first*): results appear within seconds, a
cancellation keeps the most finished files, and heavy files that hit a limit do so at the end.

- Cost = size (the uncompressed size for ZIP-based formats, already read by the check above) × a weight per
  format (xlsx weighs more: openpyxl uses many times the file size in memory). Ties are broken by path, so the
  order is deterministic.
- The order only affects processing. Output names are computed in the plan, and the summary lists files by
  path.
- The scheduler is its own module (`use_cases/scheduling.py`), so a second lane can be added later.

## Consequences

- **Gains:** real cancellation; a crash or a runaway file costs one file, not the batch; protection against zip
  bombs and memory exhaustion; quick visible progress.
- **Costs:** inter-process communication and a supervisor loop to design and test; `psutil` as a dependency;
  the worker start-up (Python + markitdown + magika) is paid once per batch and again after every kill.

## Alternatives considered

- **Threads only:** rejected; no real cancellation, no isolation, no memory limit.
- **A new process per file:** rejected; it would load markitdown and the magika model for every file.
- **Two lanes (light and heavy files) with two workers:** better latency when a huge file blocks small ones,
  but twice the memory. Deferred: added only if the benchmark shows that blocking matters.
- **Several parallel workers:** deferred for the same reason (memory with large xlsx files).
