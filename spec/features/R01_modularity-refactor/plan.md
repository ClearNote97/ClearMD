# Final pass: modularity refactor plan for ClearMD

I checked three things myself:
- **ADR numbers.** The last file in `docs/decisions/` is 0037, but `pyproject.toml:36` and four `qt/*.py` docstrings already cite ADR-0038 for feature 016. So 0038 is taken and the modularity ADR is **0039**.
- **Entry points.** `ttk/__init__` and `cli/__init__` import `main` from `app.py`. `packaging/launch_gui.py:15` imports `clearmd.frontend.ttk.main`.
- **ADR-0014:36** promises `<gui>/` with `app/ views/ components/ layout/`.

## Audit findings: accepted or rejected

### Modularity audit

| # | Verdict | Reason |
|---|---|---|
| M1 | **Accept** | The entry file is `<gui>/app.py` (≤40 lines, the owner's word), and the window goes in `<gui>/window/`. This has no function/module name clash. The `<gui>:main` entry points and `launch_gui.py:15` stay the same. |
| M2 | **Accept** | The shared GUI logic goes in `presenter/chrome/`. It holds pure functions that return value objects, checked by characterisation tests, not body comparison. ttk is the reference. `controls` is dropped. |
| M3 | **Accept** | Collaborators receive only the widgets and ports they use. A test forbids `TtkApp`/`PySideApp` as a parameter type and forbids importing `window/window.py`. Layering inside each GUI is one-way. The tiny slivers are merged. |
| M4 | **Accept** | Renames: `pickers`, `dialog_host`, `close_policy`/`closing`, `primary_button`, `display.py`, `style_names`. Presenter screens are named after the steps. |
| M5 | **Accept** | `components/dialog.py` in both GUIs. Qt's ground becomes `surface` if it does the same job (checked in P8); otherwise its docstring says what it does. `page.py` exists only if both GUIs use it; otherwise it is inlined. |
| M6 | **Accept** | Qt's `MainWindow(QWidget)` goes in `window/qt_window.py`. `layout/frame.py` holds only the arrangement. The "plain object" `PySideApp` change gets its own commit. |
| M7 | **Accept** | No re-exports from non-`__init__` modules, and no `ttk.layout`/`views.dialogs` re-exports. Tests are retargeted. |
| M8 | **Accept** | Inside `latex/`, the recursive constructs import `layout` inside the function. No wiring at import time. This also adds no stack frame (R14). |
| M9 | **Accept** | New modules under ~40 lines need a stated reason. The merges are applied in A.2. |
| M10 | **Accept** | `cursor.py`, `attributes.py`, `state.py` in all three writers, and `writer/dispatch.py`. |
| M11 | **Accept** | The `Budget` dataclass and the PySideApp-not-QWidget change come out of the move commits. |
| M12 | **Accept** | The presenter never imports `design`. `chrome` returns i18n keys and enums. |
| M13 | **Accept** | Intents are small classes built from `(session, display, backend, background)`. `Presenter` ≤150 lines. |
| M14 | **Accept** | Every GUI has `window/toolkit.py`. The window is built on a root it is given. Flet fits without changes. |
| M15 | **Accept** | `frontend/launch.py` owns every splash step after the first one, which stays in `launch_gui.py`. |

### Risk audit

| # | Verdict | Reason |
|---|---|---|
| R1 | **Accept** | HEAD is red (`ttk.brand → palette`). The fix is the first commit, and counts come from a fresh `--collect-only` (2048). |
| R2 | **Accept** | Per-module parametrised tests are left out of the count invariant. Each commit body states +N or −N. |
| R3 | **Accept** | Two techniques: module moves are verbatim with a multiset check; class decompositions are mechanical, gated by golden and characterisation tests. |
| R4 | **Accept** | P0 builds at HEAD first. If PySide6 is in the executables, the fix is a separate commit before the refactor. |
| R5 | **Accept** | ADR-0039, which supersedes ADR-0014's layout section without editing it. A spec entry, unless the owner waives it (D6). |
| R6 | **Accept** | Solved by M1 (`app.py`, no `main.py` anywhere). |
| R7 | **Accept** | The `test_007:185-186` text check is retargeted to the `launch` constant in the commit that moves the splash text. |
| R8 | **Accept** | `TtkApp` keeps its public attribute names and the one-line `show_*` forwards (~150 lines). The `MainView→ChooseView` rename gets its own commit. P7 is split into 9 commits. |
| R9 | **Accept** | `design/colors.blend` uses ttk's formula. The Qt pixel drift gets its own commit (D5). `chrome` decides only; timers stay in each GUI. Function-level differences are listed in P0. |
| R10 | **Accept** | Each new package lists itself in its own rule. An explicit `…html.writer` rule plus a checker test (no trafilatura). |
| R11 | **Accept** | `uv lock` + `uv sync` in P2. `test_entry_points` reads `pyproject.toml`. |
| R12 | **Accept** | `tests/golden/**` goes in ruff `extend-exclude` and gets `-text` in `.gitattributes`. No dates or versions in golden files. |
| R13 | **Accept** | P0 coverage is mandatory. Characterisation tests come before P9. `pdf_builder` outputs are hashed. |
| R14 | **Accept** | No extra frames on recursive paths. A depth-at-fallback characterisation test. |
| R15 | **Accept** | PySide PNG comparisons happen only in the scratchpad. The committed smoke test checks "builds and `grab()` is not null". |
| R16 | **Accept** | Screenshots always go to `--out <scratchpad>`. |
| R17 | **Partial** | Accepted: a tag per phase, revert to the last tag, merge without squash. Rejected: a separate backend branch. Two ratchets and two gate runs cost more than they give, and the owner reviews after each phase anyway. |
| R18 | **Accept** | The archive-listing diff must equal the phase's committed expected list. |
| R19 | **Accept** | A class ratchet is seeded beside the file ratchet. |
| R20 | **Accept** | `rglob`, plus a test that proves subpackages are scanned. |
| R21 | **Accept** | Rule: `Presenter.__init__` and the `detect_system_theme` import stay in `presenter.py`. |
| R22 | **Accept** | ttkbootstrap calls stay under `ttk/`. mypy runs at G0. |
| R23 | **Accept** | `read()` stays in `pdf/reader.py`. `to_latex` is patched in `blocks/equation_latex`. |
| R24 | **Accept** | Each `@cache`/`lru_cache` has exactly one definition after the move. |
| R25 | **Accept** | `worker/child.py` and `registry.py` join the not-touched list. |
| Effort | **Accept** | 120–160 h. |

---

# FINAL PLAN

## A) Target structure

### A.1 Frontend (approximate line budgets; ≤200 each; under ~40 only with a reason)

```
src/clearmd/frontend/
  design/     [stdlib] palette ~80 · metrics ~40 · typography ~20 (shared tokens: reason) · colors ~25 (blend, ttk formula)
  launch.py   ~60  splash steps after the first one, LOADED_TEXT, SMOKE_SECONDS, is_smoke(argv)
  assets/     assets/qt -> assets/pyside
  presenter/  [stdlib + backend.api/schemas + i18n; never design]
    __init__    exports unchanged
    presenter.py ~150  facade, class ≤150; __init__ and the detect_system_theme import stay here
    session ~60 · display ~70 (the _set/_show_* push to the view) · background ~50 (in_background, Generations, _later, _next_generation)
    ports models state icons system_theme   unchanged
    intents/    inputs ~95 · analysis ~110 · conversion ~140 · results ~40 · preferences ~90
                (small classes built from session, display, backend, background; none holds Presenter)
    screens/    choose ~90 (absorbs _shown/_key) · review ~70 · convert ~45 · results ~95 · primary ~75
    chrome/     header ~45 (Header) · secondary ~65 (Secondary, ready_line) · primary_gate ~40
                (PRIMARY_PAUSE_SECONDS, read at call time; gate_open) · close_policy ~50
  cli/        __init__ (main, build_parser) · app.py ~35 · parser ~75 · flow ~110 · prompts ~75 · progress ~50 · report ~90 · batch ~70
  ttk/
    __init__ (TtkApp, main) · app.py ≤40   launch steps -> toolkit root -> TtkApp(root) -> start -> smoke -> mainloop
    window/   toolkit ~65 (Tk root + DnD) · window ~150 (TtkApp: wiring; public attributes main/dialog/actions/rail/
              review/converting/results/surface kept; show_* one-line forwards = ports.View) · view ~140 · controls ~45
              · pickers ~80 · dialog_host ~95 · primary_button ~55 · inputs ~60 (presses + drops; keyboard too unless >40)
              · closing ~55 · scheduler ~62
    layout/   __init__ (empty) · fonts ~35 (toolkit units: reason) · frame ~95 (arrangement + resize)
    visuals/  style_names ~30 (shared by ≥3: reason) · themes ~40 · look ~75 · buttons ~60 · styles ~110 · shapes ~110
              · marks ~90      (brand.py and art.py are removed)
    views/    choose ~90 · review ~116 · convert ~105 · results ~109
              dialogs/ (__init__ empty) help ~45 · welcome ~45 · settings ~125 · keep_inputs ~55
    components/ dialog (base, unchanged) · inputs_card ~85 · output_card ~85 · rail ~120 · rail_art ~115 · file_list ~130
              · file_list_keys ~85 · action_bar, drop_zone, stats, surface (unchanged)
  pyside/     (was qt/; same mold)
    __init__ (PySideApp, main) · app.py ≤40
    window/   toolkit ~30 (QApplication; the shared seam: reason) · qt_window ~60 (MainWindow, one-line event forwarders)
              · window ~140 (PySideApp, a plain object) · view ~140 · controls ~45 · pickers ~80 · dialog_host ~90
              · primary_button ~55 · inputs ~60 · closing ~55
    layout/   frame ~90
    visuals/  stylesheet ~195 (pictures folded in)
    views/    choose ~90 · review ~85 · convert ~90 · results ~80 · dialogs/ help ~40 · welcome ~35 · settings ~120 · keep_inputs ~35
    components/ dialog ~40 · primitives ~65 · rail ~110 · rail_art ~60 · surface ~45 (was ground) · action_bar ~45
              · file_list ~115 · stats ~45 · drop_zone ~25 · inputs_card ~80 · output_card ~80   (page base inlined unless ttk shares it)
  flet/       (future) app.py: ft.app(target=lambda page: FletApp(page).start()); window/ (toolkit = the given page), layout/ visuals/ views/ components/
```

**Folder roles, the same in every GUI.** Each layer imports only the ones after it:

`app.py` → `window/` → `views/` → `components/` → `visuals/`, `layout/` → `frontend.design`

Allowed outside imports: `presenter`, `launch`, `schemas`, `i18n`. Never `backend.api`, and never another GUI.

### A.2 Backend splits (under `backend/services/` unless noted; "class decomp" means technique C.1b)

| Current (lines) | New files (budget) |
|---|---|
| `pdf/reader.py` 1071 | `model` 90 (with chars) · `decode` 75 · `reader` 80 (`read`; reads `MAX_DOCUMENT_PIXELS`/`MAX_CROPS`; no re-export of `opened`, importers retargeted to `pdfium.document`)<br>**`pdfium/`:** document 70, fonts 90, page_chars 100 (local aliases kept in the hot loop), page_objects 50, image_objects 60, pictures 105 (budget `list[int]` unchanged), crop 110<br>**`lines/`:** paging 80, breaks 65, assemble 120, words 40, scripts 95, script_marks 85<br>**`blocks/`:** tables_on_page 60, equation_blocks 90, equation_latex 95 (`to_latex` read here), laid_out 65 (with source) |
| `pdf/latex.py` 715 | `latex/`: symbols 95, nodes 95, envelope 55, accents 40, stacking 90, fractions 100, operators 50, brackets 95, scripts 90, row_text 100, rows 50, layout 60 (dispatcher; constructs import it inside the function), writer 40. A `params` module only if ≥2 modules read it |
| `pdf/cleaner.py` 597 | `cleaner/`: sizes 75, page_numbers 45, running 160, joining 45, render 55, headings 145 (with toc), footnotes 65, flow 70, buffer 60, items 40, writer 120 (`_Writer` 223: class decomp, done alone and last in P9), clean 65 (with params). Imports `model`, not `reader` |
| `pdf/tables.py` 298 | `tables/`: rows 85 (with model), columns 90, grid 55, build 70, find 55 |
| `pdf/equations.py` 234 | `equations/`: labels 50, bars 70, joins 55, find 75 (with model) |
| `tex/render.py` 892 | `render.py` 105 (`render_source`, `render_latex`, the `top_level` module global). `writer/`: vocab 85, state 90, structure 75, conditionals 45, expansion 45, math 100, links 65, lists 45, environments 120 (with code), floats 115, front_matter 40, commands 110 (if-chain order kept), dispatch 140. Renderer 461: class decomp. `_name_only_image` goes to `tex/images.py` |
| `tex/context.py` 423 | `tex/parsing/`: braces 65, cursor 30 (shared: reason), verbatim_args 120, definition_args 75, specs 80, walker 45, mask 65 |
| `tex/macros.py` 272 | `tex/macros/`: definition 55, collect 115, expander 130 (with budget), substitution 105 (from render.py) |
| `odt/render.py` 642 | `render.py` 100. `writer/`: vocab 70, state 75, paragraphs 65, formulas 70, frames 85, footnotes 50, inline 125, leaf_blocks 110, lists 140, blocks 90, report 45. OdtRenderer 493: class decomp |
| `odt/mathml.py` 291 | `mathml/`: tables 70, attributes 40, leaves 70, rows 50, scripts 70, translate 110 (with starmath). `MAX_FORMULAS` stays in `odt/__init__` |
| `html/render.py` 485 | `render.py` 90. `writer/` (own architecture rule, stdlib only): state 105 (with vocab), classify 65, shapes 70, runs 90, blocks 120, lists 100, tables 70 (`MAX_CELLS`). ArticleRenderer 305: class decomp |
| `conversion/inline.py` 450 | `inline/`: pieces 55, delimiters 45, styled 40, commonmark 115, emphasis 85, normalize 55, writer 95 |
| `conversion/markdown_out.py` 298 | `markdown_out/`: marks 70, code 60, escaping 90, neutralize 110 (with tidy). `__init__` with the 22 public names in `__all__` |
| `summary/pdf_report.py` 400 | `pdf_report/`: theme 45, metrics 80, text 80, canvas 75, table 55, blocks 110, report 75 |
| `summary/content.py` 225 | `model` 70 + `content` 160 |
| `worker/supervisor.py` 226 | `processes` 120 (with waiting) + `supervisor` 115 (`REAL_REGISTRY`, `VIRTUAL_HEADROOM`) |
| `detection/content.py` 203 | `text_signatures` 110 + `zip_signatures` 50 + `content` 50 |
| `use_cases/scanning.py` 215 | `scan_rules` 60 + `scanning` 160 |
| `conversion/xmltree.py` 208 | **Stays.** Security-critical; the only file planned in the 201–250 band |
| Not touched | `api/composition.py`, `use_cases/execution.py`, `registry.py`, `worker/child.py`, `html/__init__.py`, `pdf/__init__.py` |

## B) Phases

**Gates:**
- **G0, every commit:** ruff, ruff format, mypy --strict, the size/architecture/entry-point tests, and `--collect-only`. The count must equal the expected figure in the commit body; per-module parametrised ids are excluded and their ±N is stated.
- **G1, every step:** G0 plus the area's tests, plus the golden diff or the ttk screenshot diff (written to the scratchpad).
- **G2, end of each phase:** full suite in `ClearMD_dev`, PyInstaller build, `check_executables.sh`, and an archive-listing diff that must equal the committed expected list. Then tag `refactor-pN`. **Stop for the owner's review.**

| Phase | Content | Check |
|---|---|---|
| **P0 Baseline** (no commit) | Scratchpad only:<br>• fresh `wc -l` and class sizes<br>• `--collect-only` ids (2048)<br>• full-suite result, recording that HEAD is red<br>• build at HEAD and check whether PySide6 is in the executables<br>• SHA manifest of fixture, `pdf_builder` and `docs/Examples` outputs<br>• ttk screenshots ×2<br>• pyside PNGs ×2<br>• archive listing<br>• mandatory coverage on files to split<br>• ttk/Qt differences listed per function<br>• TeX nesting depth where the fallback starts | Every artefact run twice |
| **P1 Safety net** (~7 commits) | 1.0: fix the `ttk.brand → palette` rule (red to green).<br>1.1: if R4 confirms PySide6 in the executables, the exclusion fix.<br>1.2: refactor spec (unless waived, D6) + ADR-0039 *proposed*.<br>1.3: `tests/support/source_tree.py` + `test_module_size.py`: file ratchet, class ratchet, band cap, `app.py` ≤40, no mixins, floor-with-reason, tests ratchet, `EXEMPT={path: reason}`.<br>1.4: architecture rules: pyside, flet, in-GUI layering, no window-typed constructor parameters, packages list themselves, AC-04 `rglob` + a subpackage test.<br>1.5: `test_entry_points.py` (reads `pyproject.toml`).<br>1.6: `tests/golden/` (ruff exclude, `-text`) + characterisation tests (coverage gaps, recursion depth) + seam "fake was called" checks | G2 |
| **P2 qt→pyside** (2) | `git mv` the folder and assets. Extra/script `clearmd-pyside`, `uv lock` (diff = extra name only), `uv sync`, rule keys, spec, CI, AGENTS.md. Accepted ADRs are not edited. Then the pyside smoke test (builds, `grab()` not null) | G2; listing equals expected |
| **P3 design + launch** (3) | `design/` and `launch.py`; ttk imports them, duplicates removed. Separately: pyside switches to `design.colors.blend` (declared pixel drift, D5). `test_007:185` retargeted to `launch.LOADED_TEXT` | Screenshots identical |
| **P4 presenter/chrome** (2) | Pure decision functions + characterisation tables (old ttk method vs new function). ttk calls them, then pyside; Qt's differences listed in the commit body. `PRIMARY_PAUSE_SECONDS` moves (`conftest:52`, `test_main_window:728,842`) | Screenshots |
| **P5 presenter split** (3) | session/display/background → screens/ → intents/ + facade | test_presenter, test_005, screenshots |
| **P6 cli** (1) | `cli/*` as in A.1 (`app.py` stays the entry). Patch sites `test_001:481,482,571,693,694,733,759` and `test_009:212` move to the module that reads each name | test_001, test_009, golden |
| **P7 ttk** (9) | visuals → layout → views + dialogs + cards → rail_art/file_list_keys → window: dialog_host → primary_button → inputs/keyboard → closing → view + toolkit + `app.py`. `MainView→ChooseView` rename alone, last | Screenshots after each commit |
| **P8 pyside** (5) | 8a: PySideApp becomes a plain object + `qt_window` (redesign, alone). Then components, views, dialogs, window | Scratchpad PNG diff, G2 |
| **P9 PDF** (8) | tables + equations → latex → model/decode + cleaner import → pdfium → blocks + lines + slim reader → `_Writer` decomposition (alone) | Golden + manifest byte-identical after each; `page_chars` benchmark within noise |
| **P10 backend rest** (~15) | markdown_out → inline → tex/parsing → tex/macros → tex/writer moves → **Renderer decomp** → odt/mathml → odt/writer moves → **OdtRenderer decomp** → html/writer moves → **ArticleRenderer decomp** (`MAX_CELLS` in 2 tests) → summary → worker → detection → scan_rules | Golden + manifest after each; G2 per group (tex, odt+html, rest) |
| **P11 Close src** (1) | Src ratchets empty; ratchet code removed. ADR-0039 *accepted*; it supersedes ADR-0014's layout. A README per folder; `docs/architecture/README.md` | G2 + push for the CI Windows build; read the matrix |
| **P12 Tests** (~1 per file) | Split by source mirror: test_main_window, test_presenter, test_005, test_pdf_converter, test_tables, summary/test_writer, test_001, test_review_findings, the 250–400 band, test_architecture. Then `build_fixtures` (fixture bytes identical), `run_benchmark` or `EXEMPT` (D2) | Id set equal modulo path; tests ratchet empty |
| **P13 Follow-ups** (outside this refactor) | `Budget` dataclass, C6 dedupes (`growth`, `macros._inner`/`nodes.raw`, `flat_all`, surrogates, `UNREADABLE`). One commit each, gated by golden | – |

## C) Rules for the executor

1. **Two techniques.**
   - **(a) Module moves.** Verbatim: only the import block changes, plus dropping a leading `_` when a name crosses a module boundary. Reviewed with `git diff --color-moved=dimmed-zebra` and the multiset line check.
   - **(b) Class decomposition.** Methods become module functions or small collaborators. Only `self.` changes to the explicit receiver. No logic edits, no extra frames on recursive paths. Gated by golden + characterisation tests.
   - Never in either technique: dedupes, reordering, or dict-ifying an if-chain.
2. **Structure.**
   - Collaborators get only what they use, through the constructor.
   - No mixins, no base classes over ~40 lines, no import-time wiring. Recursion uses an import inside the function.
   - A subpackage needs ≥3 files.
   - A module under ~40 lines needs a reason in its docstring (shared seam, ≥2 readers, public name, or the folder's one-per-file role).
   - Import sibling modules, never your own package `__init__`.
3. **Names.**
   - The same file and class names in every GUI: `ChooseView`, `ReviewView`, `ConvertView`, `ResultsView`, `TtkApp`/`PySideApp`/`FletApp`, `window/toolkit.py`.
   - Suffixes: `_art.py` for drawing, `_keys.py` for input.
   - Every writer uses `state.py` and `dispatch.py`. No grab-bag names.
4. **Re-exports.**
   - Only in package `__init__`, only public names, always with `__all__`.
   - Public means: pyproject entry points, `presenter` exports, and backend packages imported across package boundaries.
   - No private aliases and no shims. The old file is deleted.
5. **Tests that reach internals.** Retarget them to the module that reads the name, in the move commit. Change paths and attributes only, never assertions. Every patched seam asserts its fake was called. Shared helpers come from `tests/support/`.
6. **Fixed points.**
   - `read()` stays in `pdf/reader.py`.
   - `Presenter.__init__` and the `detect_system_theme` import stay in `presenter.py`.
   - `top_level` stays a module global of `tex/render`.
   - Each cache has exactly one definition.
   - ttkbootstrap calls stay under `ttk/`.
7. **Every new folder** gets `__init__.py` and a short `README.md`. Each new module gets a one-line docstring naming its concern. Code and docs in English. No "moved from" comments.
8. **Docs.**
   - ADR-0039 "Modular layout and file size" supersedes ADR-0014's layout section. Accepted ADRs are never edited.
   - Old specs and plans are history and are not rewritten.
9. **Git.**
   - Stage by path, never `git add -A`. `docs/Examples` must stay ignored.
   - No `Co-Authored-By` line.
   - Tag each phase. Merge without squash.
   - Stop and revert to the last tag on: a golden/manifest diff, a screenshot diff, an unexpected count change, an import cycle, or an archive listing that differs from the expected list.
   - Stop for the owner's review after each phase.

## D) Decisions for the owner

1. **Entry file and window folder.** `<gui>/app.py` (≤40 lines) + `<gui>/window/`; ADR-0039 records "the template's `app/` = `app.py` + `window/`". **Recommended.** The alternative, `main.py` + `app/`, makes the `main` function hide the module.
2. **Tests under 200/250.**
   - Yes, in P12; the ratchet stops them growing until then.
   - `build_fixtures.py` (1018 lines) is split one builder per format.
   - `run_benchmark.py` (789 lines) is split, or put in `EXEMPT` to save time. **Recommended: split both.**
3. **How "the tolerance must not be abused" is enforced.**
   - At most 10% of files in the 201–250 band.
   - Class ≤150 lines.
   - `app.py` ≤40 lines.
   - No mixins.
   - Modules under ~40 lines need a reason.
   - Function length over ~60: warning only.
   - **Recommended: accept all.**
4. **Shared GUI logic in `presenter/chrome/`.** It holds decisions only (header, secondary/ready line, primary gate, close policy); timers and widgets stay in each GUI. The tokens go in `design/`. **Recommended.**
5. **Pixel drift in the Qt draft.** It adopts ttk's `blend`: 121 of ~78k colour inputs change by one channel step. The draft is unreleased. **Recommended.**
6. **Spec for the refactor.** AGENTS.md says "nothing is built without a spec". A short spec with acceptance criteria (size test, golden, screenshots, executables) is **recommended**; the alternative is that you waive it explicitly.
7. **Pre-refactor fixes.** The red `brand → palette` rule, and PySide6 inside the executables if P0 confirms it. Both get their own commits in P1. **Recommended.**

## E) Risks and effort

| Risk | Mitigation |
|---|---|
| A monkeypatch silently patches nothing | No aliases, so `setattr` raises. Seam assertions. Known sites: `PRIMARY_PAUSE_SECONDS`, `detect_system_theme`, `to_latex`, `MAX_DOCUMENT_PIXELS`/`MAX_CROPS`, `MAX_CELLS`, `top_level`, `MAX_FORMULAS`, `cli.*`, `composition.*` |
| PDF output drift; the fixtures barely touch `reader.py` | Characterisation tests for the coverage gaps before P9. Golden + `pdf_builder` hashes + the private manifest (local gate only). Benchmark |
| The six class decompositions change behaviour | Technique C.1b: one commit per class, golden + characterisation tests, the recursion-depth test |
| `_Writer`/`Flow` shared state | Field semantics and class-level defaults kept. Alone and last in P9 |
| A god-object returns, spread across collaborators | Constructor-scope rule plus the architecture tests (M3). Class ratchet |
| Construction cycle (widgets → callbacks → presenter) | Callbacks are lambdas over a fully wired window. `Presenter.__init__` never calls the view |
| A missing `__init__` or module in PyInstaller, or PySide6 leaking into the executables | P1 test, expected-listing diff at every G2, the R4 fix, the CI Windows build before merge |
| Architecture-rule holes after splits (`inline`, `markdown_out`, `html/writer`) | Each package lists itself. `html.writer` rule plus a trafilatura checker test |
| Golden files reformatted, or line endings changed on Windows | ruff `extend-exclude` + `-text` |
| Flaky screenshots or pyside PNGs | Determinism checked in P0. PNGs compared only in the scratchpad. No xdist |
| The WIP 016 base was never reviewed | Phase tags + revert. The owner reviews after each phase |

| Phase | Hours |
|---|---|
| P0 | 3–4 |
| P1 | 8–10 |
| P2 | 2–3 |
| P3 | 3–4 |
| P4 | 4–6 |
| P5 | 7–9 |
| P6 | 2–3 |
| P7 | 14–18 |
| P8 | 8–10 |
| P9 | 18–24 |
| P10 | 28–36 |
| P11 | 2–3 |
| P12 | 20–28 |
| **Total** | **~120–160 h** (~100–130 without P12), including ~30 G2 runs (~10 h of waiting) |

Files used:
- /tmp/claude-1000/-home-clearnote-trabajos-Desarrollos-ClearMD/f21bf619-8a39-487a-a8d0-858c5174bae3/scratchpad/inventory.md
- /home/clearnote/trabajos/Desarrollos/ClearMD/docs/decisions/0014-template-aligned-src-layout.md
- /home/clearnote/trabajos/Desarrollos/ClearMD/pyproject.toml
- /home/clearnote/trabajos/Desarrollos/ClearMD/src/clearmd/frontend/ttk/__init__.py
- /home/clearnote/trabajos/Desarrollos/ClearMD/src/clearmd/frontend/cli/__init__.py
- /home/clearnote/trabajos/Desarrollos/ClearMD/packaging/launch_gui.py