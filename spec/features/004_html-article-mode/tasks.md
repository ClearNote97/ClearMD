# Tasks — Feature 004: HTML article mode

> Executable steps, in order. Test first. Plan: [`plan.md`](./plan.md) · Criteria: [`spec.md`](./spec.md).

- [ ] **T01 — Fixtures.** `tests/fixtures/html/`: `news.html`, `no_article.html`, `hostile.html`; reproducible.
- [ ] **T02 — The strategy through the pipeline.** Strategy in the plan, the request, the registry, the CLI
      flag, the setting and the summary; full stays the default and nothing else moves (AC-01, AC-03).
- [ ] **T03 — Shared XML tree.** `xmltree.py` to `conversion/`; odt unchanged.
- [ ] **T04 — The article converter.** trafilatura's XML rendered through `markdown_out`; images as
      placeholders; the full-page fallback with its note (AC-02, AC-04 – AC-06, AC-09, AC-10).
- [ ] **T05 — Guarantee and acceptance.** The CommonMark check and fuzz for article mode;
      `tests/acceptance/test_004_html_article_mode.py` (AC-07, AC-08).
- [ ] **T06 — Benchmark and close.** An article case in the benchmark and `limits.py` (AC-11); READMEs,
      architecture, roadmap, spec ticked; gate; review by `code-reviewer` and a security audit with runnable
      proofs, then an adversarial verification of the fixes; ADR-0025 accepted.
