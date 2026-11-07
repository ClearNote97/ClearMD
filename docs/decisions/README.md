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
| [0014](./0014-template-aligned-src-layout.md) | `src/` layout aligned with the ClearNote_Dev template | accepted; layout section superseded by 0039 |
| [0015](./0015-conversion-worker-process.md) | Worker process, resource limits and a cost-ordered queue | accepted |
| [0016](./0016-output-layout-and-summary.md) | Output layout, chosen output folder and `Resumen_ClearMD.md` | accepted; folder renamed by 0019 |
| [0017](./0017-english-default-language.md) | English by default, no OS language detection | accepted |
| [0018](./0018-python-range-and-installation.md) | Python 3.12–3.14 and ways to install | accepted |
| [0019](./0019-outputmd-and-v2-tools.md) | `OutputMD/` for results; room for the v2 tools (merge, split) | accepted; Tools window superseded by 0043 |
| [0020](./0020-non-root-dev-container.md) | The dev container runs as a non-root user with the host's UID | accepted |
| [0021](./0021-content-detection-only-without-extension.md) | Content detection only for files without an extension | accepted |
| [0022](./0022-latex-includes-macros-and-notes.md) | LaTeX: includes, the author's macros and conversion notes | accepted; refined by 0023 |
| [0023](./0023-latex-hardening-after-review.md) | LaTeX: includes as inserted text, images never fetched, a file never fails whole | accepted |
| [0024](./0024-opendocument-converter.md) | OpenDocument text: XML read safely, images as placeholders, formulas as LaTeX | accepted |
| [0025](./0025-html-article-mode.md) | HTML article mode: trafilatura finds the article, ClearMD writes it | accepted; refined after review |
| [0026](./0026-presenter-and-ttk-gui.md) | The presenter and the first GUI (ttkbootstrap) | accepted; refined by 0027 |
| [0027](./0027-visual-identity.md) | Visual identity: the rail and cards, teal, the C·M↓ logo, own file icons | accepted |
| [0028](./0028-ci-and-executables.md) | CI on Linux and Windows; one-file executables built and checked on GitHub Actions | accepted; refined by 0037 |
| [0029](./0029-step-navigation.md) | Free navigation between the steps; one primary action per step, with its reason when disabled | accepted |
| [0030](./0030-pdf-reader.md) | PDF read by PDFium and cleaned by ClearMD: spaces, glyph codes, running lines, paragraphs, headings | accepted |
| [0031](./0031-human-summary.md) | A summary in human language, and its PDF in the app's look | accepted |
| [0032](./0032-light-executable.md) | A light executable: own detection and Excel converter, two languages of babel | accepted |
| [0033](./0033-images-in-a-folder.md) | A document's images in a folder next to its Markdown | accepted |
| [0034](./0034-pdf-tables-and-equations.md) | A PDF's tables, equations and table of contents | accepted; refined by 0035, 0036 |
| [0035](./0035-pdf-sub-and-superscripts.md) | A PDF's sub- and superscripts | accepted |
| [0036](./0036-equations-as-latex.md) | A PDF's equations rebuilt as LaTeX | accepted |
| [0037](./0037-code-signing.md) | The Windows executables signed by SignPath | accepted |
| [0038](./0038-pyside-gui-delivery.md) | The PySide6 GUI, delivered as a folder next to the ttk app | accepted |
| [0039](./0039-modular-layout-and-file-size.md) | Modular layout and file size: ≤ 200 lines (250 at most), one layout for every GUI | accepted |
| [0040](./0040-windows-installer.md) | A Windows installer and uninstaller, with Inno Setup | accepted |
| [0041](./0041-installer-look.md) | The installer looks like ClearMD | accepted |
| [0042](./0042-flet-gui-delivery.md) | The flet GUI, delivered as a folder with its own window program | accepted |
| [0043](./0043-local-toolkit-for-ai.md) | A local toolkit that prepares documents for AI: Convert, Split, Merge | accepted |
