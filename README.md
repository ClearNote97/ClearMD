<div align="center">

<img src="./src/clearmd/frontend/assets/logo/clearmd-app-128.png" alt="ClearMD" width="96">

# Clear·MD

**Prepare your documents for AI — 100% local: ClearMD never uses the internet.**

_Three tools: **Convert** PDF, Word, OpenDocument, PowerPoint, Excel, HTML, CSV, EPUB, notebooks, LaTeX (equations kept),
e-mails, Rich Text and subtitles to clean Markdown; **Split** a large file into parts that fit an AI; **Merge** several into
one. Built first for people who never open a terminal._

![Python](https://img.shields.io/badge/Python-3.12%E2%80%933.14-3776AB?logo=python&logoColor=white)
![markitdown](https://img.shields.io/badge/markitdown-0.1.9-0078D4?logo=microsoft&logoColor=white)
![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=uv&logoColor=white)
![Dev Container](https://img.shields.io/badge/Dev-Container-2496ED?logo=docker&logoColor=white)
![Spec-Driven](https://img.shields.io/badge/Spec--Driven-Development-6E40C9)
![made with Claude Code](https://img.shields.io/badge/made%20with-Claude%20Code-D97757?logo=anthropic&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/status-under%20construction-orange)

### [⬇️ Download ClearMD for Windows](https://github.com/ClearNote97/ClearMD/releases/latest)

<sub>Open the newest release and take <code>ClearMD-Setup-&lt;version&gt;.exe</code> (about 30 MB, the Classic App): it installs and uninstalls like any Windows program. <code>ClearMD-Setup-Full-&lt;version&gt;.exe</code> adds the Modern App, the Mobile-Style App and the Command Line. Linux: the <code>.tar.gz</code> of the same release.</sub>

[Leer en español](./README.es.md)

</div>

> 👋 **Want to see my other projects?** → **[github.com/ClearNote97](https://github.com/ClearNote97)**

---

## 🧩 The problem

> **Useful content is trapped in heavy formats, and the tools to free it are not made for everyone.**

Notes for Obsidian, documentation for GitHub, context for an LLM: all of them want Markdown, while the content
lives in PDFs, Word files and spreadsheets. The existing answers are command-line libraries, web services that
make you **upload your documents**, or single-format converters. None of them is made for someone who has never
opened a terminal — and private documents (contracts, medical records, unpublished theses) should never have to
leave the machine.

---

## 🧠 How I solved it

The value is in the method — a small product built like a serious one:

1. **Decisions first, recorded.** Every non-trivial choice is an ADR in [`docs/decisions/`](./docs/decisions/)
   (23 so far), with the rejected alternatives and the costs: why PySide6 and not PyQt6, why no pandoc, why no
   database, why a worker process.
2. **Spec before code.** Under **Spec-Driven Development**, [`spec/`](./spec/) says what *must* be true: feature
   001 has 44 acceptance criteria and 002 has 22, and a test fails if any criterion of any feature has no
   acceptance test.
3. **A core that knows nothing of the outside.** Hexagonal architecture laid out with the `backend/` and
   `frontend/` folders of my template: the use cases import only the standard library; markitdown and magika live
   behind ports and run **only in a worker process**.
4. **Untrusted files, handled as such.** Zip bombs are caught from the archive index before anything is
   decompressed; links are never followed; each file runs under a time limit and a memory limit (with a hard cap
   from the OS); a link planted in the output folder cannot redirect a write; Ctrl+C stops at once. A LaTeX
   thesis is followed only inside its folder and its macros expand within a budget (a macro bomb stops), and the
   Markdown never holds HTML, a remote image or a link the document did not write as LaTeX — checked in the
   test suite by a CommonMark parser and a seeded fuzz. An `.odt` is read with ClearMD's own XML reader (no
   `DOCTYPE`, limits on size and depth), with the same guarantee and a budget so that no small file can
   multiply into a huge Markdown. A web page in **article mode** (`--html article`) keeps only its article —
   no menus, cookie banners or footers — written by ClearMD with the same guarantee: its images are never
   fetched, and a page with no article is written whole by ClearMD too.
5. **Measured, not guessed.** Benchmarks ([001](./docs/benchmarks/001-conversion-limits.md),
   [002](./docs/benchmarks/002-tex-converter.md), [003](./docs/benchmarks/003-odt-converter.md),
   [004](./docs/benchmarks/004-html-article-mode.md)) set the limits and the speed of each format: xlsx is the memory bottleneck, a PDF reads ~100 pages/s with PDFium (ADR-0030), a 300-page
   LaTeX thesis takes ~3 s and a 300-page `.odt` report under a second. Files are converted from
   the cheapest to the most expensive, and the time left is estimated from the real speed of the batch.
6. **Reviewed by independent eyes.** A code review, a security audit and an adversarial verification of the
   fixes — which found real gaps in the first round of fixes, closed before shipping. For the LaTeX and the
   OpenDocument converters it took three rounds each, for the article mode two: every one is in the history,
   with the test that reproduces every finding.

> 🤖 I built this with an AI agent (**Claude Code**): I direct — I define the problem, decide the design and
> review every step; the agent executes and leaves everything traced.

---

## 👀 A look

**The desktop app** — a real batch, from choosing a folder to the results (no internet involved):

![ClearMD converting a folder](./docs/screenshots/007/flow-light-en.gif)

| Choose | Review | Results |
|---|---|---|
| ![Choose](./docs/screenshots/007/1-choose-light-en.png) | ![Review](./docs/screenshots/007/2-review-light-en.png) | ![Results](./docs/screenshots/007/4-results-dark-en.png) |

Light and dark, English and Spanish: every screen is in [`docs/screenshots/007/`](./docs/screenshots/007/).

**The command line** — a mixed folder, with a password-protected PDF, a document without extension, two files that would get the same
name, and a zip bomb disguised as a Word file:

```text
$ clearmd Thesis/
– Skipped: invoice.docx — grows 338 times when decompressed; limit 100 (possible zip bomb). If you trust
  it, save a new copy from its program.
[1/5] Report.docx
[2/5] scan · less than a minute left
[3/5] report.pdf · less than a minute left
[4/5] data.xlsx · less than a minute left
[5/5] contract.pdf · less than a minute left
✗ Failed: contract.pdf — This file is password-protected. Remove the password and try again.
4 converted · 1 skipped · 1 failed
Results: ClearMD_Output
```

And the `Resumen_ClearMD.md` it leaves next to the results:

| Source | Output | Format | Time |
|---|---|---|---|
| `Thesis/Report.docx` | `OutputMD/Thesis/Report (docx).md` | DOCX | <1 s |
| `Thesis/scan` | `OutputMD/Thesis/scan.md` | DOCX, detected by content | <1 s |
| `Thesis/report.pdf` | `OutputMD/Thesis/report (pdf).md` | PDF | <1 s |
| `Thesis/chapters/data.xlsx` | `OutputMD/Thesis/chapters/data.md` | XLSX | <1 s |

_Plus the failed and skipped files with a plain-words reason, and the history of earlier batches._

---

## 🚧 Status

| Feature | | |
|---|---|---|
| **001** Batch conversion — backend + CLI | ✅ done | 512 tests · reviewed |
| **002** `.tex` converter (math preserved, no pandoc) | ✅ done | 807 tests in total · reviewed |
| **003** `.odt` converter (standard library only) | ✅ done | 1085 tests in total · reviewed |
| **004** HTML article mode | ✅ done | 1287 tests in total · reviewed |
| **005** First desktop app (ttkbootstrap) | ✅ done | 1622 tests in total · reviewed |
| **006** CI + Windows/Linux executables | ✅ done | CI on Linux and Windows · executables checked by a real batch |
| **007** Free navigation, checkboxes, a smoother window | ✅ done | v0.2.0 · reviewed |
| **008** PDF quality: PDFium reads, ClearMD cleans | ✅ done | v0.3.0 · reviewed |
| **009** A summary in human language, and its PDF | ✅ done | v0.4.0 · reviewed · [samples](./docs/screenshots/009/) |
| **010** A light executable: about 90 MB to 40 | ✅ done | v0.5.0 · reviewed |
| **011** Window polish II: the rail's sections, the page's card, every hint | ✅ done | v0.6.0 · reviewed |
| **012** A document's images in a folder next to its Markdown (optional) | ✅ done | v0.7.0 · reviewed |
| **013** PDF tables (after Camelot), equations and tables of contents | ✅ done | v0.8.0 · reviewed |
| **014** Sub- and superscripts in PDFs, one gutter, faded waiting cards | ✅ done | v0.9.0 · reviewed |
| **015** A PDF's equations as LaTeX | ✅ done | v0.10.0 |
| **016** The same app in PySide6 (Qt) | ✅ done | v0.11.0 |
| **017** Windows installer and uninstaller | ✅ done | v0.12.0 |
| **018** The flet app — ClearMD 1.0 | ✅ done | v1.0.0 · [screenshots](./docs/screenshots/018/) |
| **019** The installer looks like ClearMD (light and dark) | ✅ done | v0.13.2 · [screenshots](./docs/screenshots/019/) |
| **020** The summary as a PDF alone | ✅ done | v1.1.0 |
| **021** flet's empty list as two large tiles; titles in Title Case | ✅ done | v1.2.0 · [screenshots](./docs/screenshots/018/) |
| **022** Security policy, contributing guide, issue forms; checksums with every release | ✅ done | v2.0.0 |
| **023** Start screen and Split a PDF — ClearMD 2.0 | ✅ done | v2.0.0 · [screenshots](./docs/screenshots/016/) |
| **024** Split into parts that fit an AI (about N words); Split takes Markdown | ✅ done | v2.1.0 |
| **025** "Split the Large PDFs" from Convert | ✅ done | v2.2.0 |
| **026** Merge documents into one Markdown or one PDF | ✅ done | v2.3.0 |
| **027** Split text, CSV and Excel | ✅ done | v2.4.0 |
| **028** Incremental mode: replace a result only if its original changed | ✅ done | v2.5.0 |
| **029** E-mails, Rich Text and subtitles | ✅ done | v2.6.0 |
| **030** The queue measured: one worker in cost order stays (ADR-0050) | ✅ done | — |
| **031** Ready for PyPI: metadata, a checked build, Trusted Publishing (off until enabled) | ✅ done | v2.7.0 |
| **032** Merge's order (move up/down), "What Next?" with Go Back Home, the start screen alike | ✅ done | v2.8.0 |
| **033** "What Next?" as the three tools and one box for the files | ✅ done | v2.8.1 |
| **034** Never lose or misreport work: earlier parts and merges kept, CSV columns, images | ✅ done | v2.9.0 |
| **035** Honest signals, a Help that guides, the full reason and where the files are | ✅ done | v2.10.0 |
| **036** Clear messages, page N of M, Copy Details, plain installer names | ✅ done | v2.10.0 |
| **037** A light installer (the Classic App) and a full one | ✅ done | v2.10.0 |
| **038** Say only what is true (encodings, N parts, tables, messages) and start faster | ✅ done | v2.11.0 |
| **039** Truth for the AI (hidden text, remote images, short Windows texts), care for the person, a true installer | ✅ done | v2.12.0 |
| **040** Promises kept in the hard cases: empty results fail, one output door, readable marks, visible focus | ✅ done | v2.13.0 |

Full plan in the [roadmap](./spec/roadmap.md). ClearMD has a **command line** and the same **desktop app** in three toolkits,
ttkbootstrap (`clearmd-ttk`), PySide6 (`clearmd-pyside`, [screenshots](./docs/screenshots/016/)) and flet
(`clearmd-flet`, [screenshots](./docs/screenshots/018/)), all also as Windows and Linux executables built and
checked by CI.

---

## ▶️ How to run

**Install it on Windows** (recommended): from the [latest release](https://github.com/ClearNote97/ClearMD/releases/latest),
download `ClearMD-Setup-….exe` and open it: it installs the Classic App, for your user only (no administrator); then
open ClearMD from the Start menu. Most people need nothing else. `ClearMD-Setup-Full-….exe` lets you choose, each
explained: the Classic App (the lightest, the default), the Modern App (made with Qt), the Mobile-Style App (made with
flet), the Command Line, or all of them.
**If you use a screen reader**, download `ClearMD-Setup-Full-….exe` and choose the Modern App: it works best with
one (the Classic App cannot be read by screen readers).

**Or download the app** (nothing to install): `ClearMD-…-windows.exe` for Windows or `ClearMD-…-linux.tar.gz` for
Linux, then open it with a double click.
Windows may warn that the program is not recognized, because it is not code-signed yet: *More info → Run anyway*.
Signing is on its way: [Code signing policy](./CODE_SIGNING.md).
Each file can be checked against the release's `SHA256SUMS.txt` ([how](./SECURITY.md#checking-a-download)).
The same app drawn with Qt is `ClearMD-Qt-…-windows.zip`: unzip it and open `ClearMD-Qt.exe` inside the folder
(a folder, not one file: Qt's libraries stay replaceable, as their LGPL license asks; on Linux it is in the archive).
The same app drawn with flet (Flutter) is `ClearMD-Flet-…-windows.zip`: unzip it and open `ClearMD-Flet.exe` inside
the folder. It carries flet's own window program, so it never downloads anything; files are added with its two
buttons (flet cannot receive dragged files). On Linux it needs GTK 3, and `zenity` for its file dialogs.
The one-file app's first start takes a few seconds while it unpacks itself; the installed one opens in a couple.

**From the repository**, for the command line (the package is not on PyPI yet):

```bash
uv tool install git+https://github.com/ClearNote97/ClearMD   # recommended: same tool as the dev stack
# or: pip install git+https://github.com/ClearNote97/ClearMD  (Python 3.12–3.14)

clearmd-ttk                              # the desktop app
clearmd report.pdf notes.docx            # files
clearmd ~/Documents/project              # a whole folder, subfolders included
clearmd thesis/ --output-root ~/Desktop  # results in ~/Desktop/ClearMD_Output
clearmd project/ --dry-run               # see the plan, write nothing
clearmd report.pdf --lang es             # messages in Spanish
clearmd saved_page.html --html article   # only the page's article
```

| Option | What it does |
|---|---|
| `--overwrite` / `--skip` | What to do with outputs that already exist. Without either, ClearMD asks once. |
| `--recursive` / `--no-recursive` | Include subfolders or not (default: yes). |
| `--output-root DIR` | Create `ClearMD_Output` inside `DIR`. |
| `--dry-run` | Show what would happen; write nothing. |
| `--open` | Open the results folder when done. |
| `--html {full,article}` | Web pages: the whole page (default) or only its article. |
| `--lang {en,es}` | Language for this run. |
| `-q`, `--quiet` | Only the summary and errors. |

**Exit codes:** `0` all converted · `1` some file failed or was stopped · `2` usage error or no valid input ·
`3` outputs exist and nobody can answer · `130` cancelled. **Settings** (optional): `settings.toml` in your
user configuration folder (on Linux `~/.config/ClearMD/`) — `language = "es"`, `on_existing_output = "skip"`,
`recursive = false`, `html_strategy = "article"`…

**Uninstall:** installed with `ClearMD-Setup`, remove it from *Settings → Apps → Installed apps* (or *Uninstall
ClearMD* in the Start menu); it asks whether to delete your settings too, and never touches your documents. Without
the installer, the app installs nothing: delete the executable. `uv tool uninstall clearmd` (or
`pip uninstall clearmd`) removes the command line. ClearMD's settings, if any, stay in a folder of their own:
delete it too to leave no trace (`%LOCALAPPDATA%\ClearMD`, that is `C:\Users\<you>\AppData\Local\ClearMD`, on
Windows; `~/.config/ClearMD` on Linux).

> 🔒 ClearMD never uses the internet. If you save the results in a folder synced by OneDrive, Google Drive or
> Dropbox, that app may upload them — that is the sync app, not ClearMD.

---

## 📦 What it produces

```
ClearMD_Output/          next to what you chose (or in --output-root)
  Resumen_ClearMD.md     what was converted (old name → new name, format, time), stopped, failed or skipped,
                         and the history of earlier batches
  OutputMD/              the Markdown files, mirroring your folders
```

---

## 🗂️ Structure

```
.
├── src/clearmd/
│   ├── backend/
│   │   ├── api/         # the facade every interface calls + the composition root
│   │   ├── schemas/     # immutable data: plans, reports, limits, error codes (stdlib only)
│   │   ├── use_cases/   # scan → plan → order → execute → report, and the ports (stdlib only)
│   │   └── services/    # worker process, markitdown and magika adapters, summary, settings
│   ├── frontend/cli/    # the command-line interface (the GUIs arrive here, one folder each)
│   └── i18n/            # EN/ES message catalogs
├── spec/                # ★ Spec-Driven Development: constitution, roadmap, feature specs, UX contract
├── docs/                # architecture, 25 ADRs, benchmarks
├── tests/               # unit (mirror of src) · acceptance (one per criterion) · fixtures · benchmark
└── .devcontainer/       # reproducible environment (non-root, uv)
```

---

## 🛠️ Stack

**Python 3.12–3.14** · **[markitdown](https://github.com/microsoft/markitdown)** (conversion) ·
**[magika](https://github.com/google/magika)** (detection by content) ·
**[trafilatura](https://github.com/adbar/trafilatura)** (finding a page's article) ·
**[pylatexenc](https://github.com/phfaist/pylatexenc)** (reading LaTeX) · **psutil** (worker limits) ·
**platformdirs** · **[ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap)** + **tkinterdnd2** + **Pillow**
(the desktop app) · **pytest · ruff · mypy --strict** · **uv** · **Dev Container + Docker**.

**Base template:** [ClearNote_Dev](https://github.com/ClearNote97/ClearNote_Dev) — my flagship template for
Python development under Spec-Driven Development. ClearMD was born from it and pruned: no database, no web
backend — a desktop tool ([ADR-0009](./docs/decisions/0009-template-pruning.md)).

**Development:** open the folder in VS Code → *Reopen in Container*; then `uv run pytest`,
`uv run ruff check .`, `uv run mypy`. Working with AI agents follows [`README_AGENTS.md`](./README_AGENTS.md).

---

## 🙏 Credits

- **Author:** MSc. Nicolás Enrique Valencia Santiago.
- **Work partner:** AI agent (Claude / Claude Code, within the [Helix](https://github.com/ftuga/helix_asisten)
  framework by [ftuga](https://github.com/ftuga)).
- **Built on these libraries, with thanks to their authors.** ClearMD's own work is what comes out: the
  Markdown it writes, its guarantee and its notes; these find and read the content.

  | Library | What it does in ClearMD | License |
  |---|---|---|
  | [markitdown](https://github.com/microsoft/markitdown) (Microsoft) | converts Word, PowerPoint, Excel, HTML, CSV, EPUB and notebooks | MIT |
  | [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) with [PDFium](https://pdfium.googlesource.com/pdfium/) (Google) | reads the text of PDFs for ClearMD's PDF converter | Apache-2.0 / BSD-3-Clause |
  | [magika](https://github.com/google/magika) (Google) | detects the format of files without an extension | Apache-2.0 |
  | [trafilatura](https://github.com/adbar/trafilatura) (Adrien Barbaresi) | finds the article of a web page (article mode) | Apache-2.0 |
  | [pylatexenc](https://github.com/phfaist/pylatexenc) (Philippe Faist) | reads LaTeX for ClearMD's `.tex` converter | MIT |
  | [psutil](https://github.com/giampaolo/psutil) (Giampaolo Rodolà) | measures the worker's memory | BSD-3-Clause |
  | [platformdirs](https://github.com/tox-dev/platformdirs) | finds where the settings live on each system | MIT |
  | [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) (Israel Dryer) | themes for the desktop app (tkinter) | MIT (parts Apache-2.0 or BSD-2-Clause) |
  | [tkinterdnd2](https://github.com/Eliav2/tkinterdnd2) (with tkdnd) | dropping files on the window | MIT |
  | [Pillow](https://github.com/python-pillow/Pillow) | draws the window's rounded shapes and ClearMD's icons | MIT-CMU |

  Each one brings its own dependencies, under their own licenses (all permissive); `uv.lock` lists them.

- **Inspired by [Camelot](https://github.com/camelot-dev/camelot)** (Vinayak Mehta and contributors, MIT): ClearMD
  finds a PDF's tables after its *stream* and *lattice* methods, written anew on PDFium's text and drawing
  (ADR-0034); Camelot itself is not a dependency.

## ⚖️ License

[MIT](./LICENSE) © 2026 Nicolás Enrique Valencia Santiago.
