# docs/decisions — ADRs (Architecture Decision Records)

One file per non-trivial decision: `NNNN-short-title.md`. Minimum format:

```
# ADR-0001: <title>
- Status: proposed | accepted | superseded by ADR-XXXX
- Date: YYYY-MM-DD
- Context: what problem/forces motivate the decision
- Decision: what was decided
- Consequences: what is gained and what it costs
```

Optional: **Alternatives considered** (what was rejected and why).
An accepted ADR is not rewritten to change the decision: a new one is written that supersedes it.

## Index

| ADR | Decision | Status |
|---|---|---|
| [0001](./0001-core-and-adapters.md) | Pure core with ports and adapters (CLI + 3 GUIs + presenter) | accepted; module names superseded by 0014 |
| [0002](./0002-no-database.md) | No database; preferences in TOML | accepted |
| [0003](./0003-pyside6-over-pyqt6.md) | PySide6-Essentials instead of PyQt6 (license) | accepted |
| [0004](./0004-hybrid-engine-with-markitdown.md) | Hybrid engine: markitdown behind a port + own converters | accepted |
| [0005](./0005-fully-local.md) | 100% local: documents never leave the machine | accepted |
| [0006](./0006-own-converters.md) | Own converters: .tex, .odt and HTML article mode | accepted; refined by 0022 |
| [0007](./0007-real-package-src-layout.md) | Real package with `src/` layout | accepted; README rule superseded by 0014 |
| [0008](./0008-dev-only-container.md) | Container for development; executables from CI | accepted |
| [0009](./0009-template-pruning.md) | Pruning of the ClearNote_Dev template | accepted |
| [0010](./0010-batch-detection-and-output-folder.md) | Batch, autodetection and the `ClearMD_Output` folder | accepted; outputs superseded by 0016, extended by 0015, detection narrowed by 0021 |
| [0011](./0011-repository-language.md) | Repository language: English, with a Spanish README | accepted; corrected by 0014 |
| [0012](./0012-bilingual-app-and-shared-settings.md) | Bilingual app (TOML catalogs) and one shared settings file | accepted; language resolution superseded by 0017 |
| [0013](./0013-non-technical-users-first.md) | Designed for non-technical users first, with a shared UX contract | accepted |
| [0014](./0014-template-aligned-src-layout.md) | `src/` layout aligned with the ClearNote_Dev template | accepted |
| [0015](./0015-conversion-worker-process.md) | Worker process, resource limits and a cost-ordered queue | accepted |
| [0016](./0016-output-layout-and-summary.md) | Output layout, chosen output folder and `Resumen_ClearMD.md` | accepted; folder renamed by 0019 |
| [0017](./0017-english-default-language.md) | English by default, no OS language detection | accepted |
| [0018](./0018-python-range-and-installation.md) | Python 3.12–3.14 and ways to install | accepted |
| [0019](./0019-outputmd-and-v2-tools.md) | `OutputMD/` for results; room for the v2 tools (merge, split) | accepted |
| [0020](./0020-non-root-dev-container.md) | The dev container runs as a non-root user with the host's UID | accepted |
| [0021](./0021-content-detection-only-without-extension.md) | Content detection only for files without an extension | accepted |
| [0022](./0022-latex-includes-macros-and-notes.md) | LaTeX: includes, the author's macros and conversion notes | accepted; refined by 0023 |
| [0023](./0023-latex-hardening-after-review.md) | LaTeX: includes as inserted text, images never fetched, a file never fails whole | accepted |
| [0024](./0024-opendocument-converter.md) | OpenDocument text: XML read safely, images as placeholders, formulas as LaTeX | accepted |
| [0025](./0025-html-article-mode.md) | HTML article mode: trafilatura finds the article, ClearMD writes it | accepted; refined after review |
