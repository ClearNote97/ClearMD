# Tasks — Feature 002: `.tex` converter

> Executable steps, in order, in vertical slices; each slice ends with something that runs end to end and the
> acceptance tests of the criteria it covers. Test first. Plan: [`plan.md`](./plan.md) · Criteria:
> [`spec.md`](./spec.md).

## Slice A — A paper, end to end

Goal: `clearmd paper.tex` writes a faithful `paper.md` through the worker, with notes for what it could not do.

- [ ] **T01 — Fixtures.** `tests/fixtures/tex/` from `build_fixtures.py`: `paper.tex`, the thesis folder,
      `latin1.tex`, `unknown.tex`, the `hostile/` set, `no_extension_latex`; a test that they are reproducible.
- [ ] **T02 — Notes through the pipeline.** `schemas/notes.py`; `ConversionResult`; `ConversionOutcome.notes`;
      the worker protocol; markitdown returns no notes; summary section and CLI line; EN/ES catalog keys
      (AC-18 – AC-19 at unit level).
- [ ] **T03 — Detection and the format.** `FormatId.TEX`, `.tex`, magika `latex`; provisional limits; the
      registry routes TEX to a converter skeleton (AC-01 – AC-03).
- [ ] **T04 — Reading.** `source.py`: UTF-8, `inputenc`, detected encoding with a note (AC-20).
- [ ] **T05 — Rendering the subset.** `render.py` + `tables.py`: structure, emphasis, lists, quotes, links,
      footnotes, code, math, citations, references, accents, layout-only commands, unknown commands kept and
      recorded, malformed input recovered (AC-04 – AC-13, AC-18, AC-21).

## Slice B — A thesis

- [ ] **T06 — Includes.** `includes.py` with every refusal and limit; rendering follows allowed includes with the
      shared state (AC-14, AC-15).
- [ ] **T07 — Macros.** `macros.py`: first-pass collection, the context with user specs, expansion in text and
      math, definitions from included files, the budget and its note (AC-16, AC-17).
- [ ] **T08 — Images.** Paths relative to the output `.md`, `\graphicspath`, extension lookup; the request carries
      the target path (AC-13).

## Slice C — Measured and closed

- [ ] **T09 — Acceptance sweep.** `tests/acceptance/test_002_tex_converter.py`, one test per AC-01 … AC-22; the
      meta-test covers every feature folder.
- [ ] **T10 — Benchmark.** A `.tex` case in `run_benchmark.py`; measured `SECONDS_PER_MIB[TEX]` and
      `MEMORY_PER_MIB[TEX]`; `docs/benchmarks/` updated (AC-22).
- [ ] **T11 — Close the feature.**
  - `docs/architecture/README.md` and both READMEs (formats, status table).
  - Tick the roadmap and the spec.
  - Gate (pytest, ruff, mypy strict).
  - Review by `code-reviewer` and `security-auditor` (includes and macros), then an adversarial verification of
    the fixes.
  - Any new non-trivial decision becomes an ADR.
