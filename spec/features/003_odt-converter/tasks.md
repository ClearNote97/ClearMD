# Tasks — Feature 003: `.odt` converter

> Executable steps, in order, in vertical slices; each slice ends with something that runs end to end and the
> acceptance tests of the criteria it covers. Test first. Plan: [`plan.md`](./plan.md) · Criteria:
> [`spec.md`](./spec.md).

## Slice A — A report, end to end

Goal: `clearmd report.odt` writes a faithful `report.md` through the worker, safely, with its notes.

- [x] **T01 — Fixtures.** `tests/fixtures/odt/` from `build_fixtures.py` (stdlib `zipfile`, ODF 1.3):
      `report.odt` (the whole text subset), `merged.odt`, `revisions.odt`, `unknown.odt`, `spreadsheet.odt`
      (an `.ods` renamed), `encrypted.odt`, `damaged.odt`, `no_extension_odt`, and the `hostile/` set
      (DOCTYPE, entities, depth, element count, huge text, `../` objects, a zip bomb); reproducible.
- [x] **T02 — The shared output module.** `markdown_out.py` out of `tex/render.py`, no behaviour change: the
      `.tex` suite, the golden paper and the output-guarantee test pass untouched.
- [x] **T03 — The format.** `FormatId.ODT`, `.odt`, magika `odt`, `ZIP_BASED`, provisional limits; registry →
      `OdtConverter` skeleton; the architecture test forbids non-stdlib imports in `odt/` (AC-01 – AC-03).
- [x] **T04 — Reading safely.** `package.py` + `xmltree.py`: mimetype, encryption, size caps, the pyexpat tree
      with DOCTYPE refused and its limits (AC-04, AC-16, AC-17).
- [ ] **T05 — Styles and the text subset.** `styles.py` + `render.py` + `tables.py`: headings, title,
      emphasis, lists, links, notes, quotations, code, spaces, fields, hidden and generated content, tables
      with merged cells, revisions, unknown elements; golden `report.md` (AC-05 – AC-09, AC-13 – AC-15).

## Slice B — Images and formulas

- [ ] **T06 — Images.** Placeholders from title/description/name, the count note; nothing extracted (AC-10).
- [ ] **T07 — Formulas.** `mathml.py`: the subset to LaTeX, display vs inline, the StarMath fallback, object
      count and size limits, references inside the archive only (AC-11, AC-12, AC-19).

## Slice C — Measured and closed

- [ ] **T08 — Guarantee and acceptance sweep.** The `.odt` corpus and fuzz in `test_output_guarantee.py`;
      `tests/acceptance/test_003_odt_converter.py`, one test per AC-01 … AC-20 (AC-18).
- [ ] **T09 — Benchmark.** An `.odt` case in `run_benchmark.py`; measured factors in `limits.py`;
      `docs/benchmarks/003-odt-converter.md` (AC-20).
- [ ] **T10 — Close the feature.**
  - Real `.odt` files exported by LibreOffice (installed provisionally in the dev container, by the author's
    decision) convert as expected; they stay committed as fixtures. **Uninstall LibreOffice from the container.**
  - `docs/architecture/README.md` and both READMEs (formats, status table); roadmap and spec ticked.
  - Gate (pytest, ruff, mypy strict).
  - Review by `code-reviewer` and `security-auditor`, then an adversarial verification of the fixes with the
    CommonMark parser.
  - Any new non-trivial decision becomes an ADR; ADR-0024 becomes "accepted".
