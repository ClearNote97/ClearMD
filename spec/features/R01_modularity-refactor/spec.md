# Refactor R01 — Modular layout and file size

A refactor, not a feature: nothing the user sees changes. Its folder is `R01` so the feature numbers
(016 PySide6, 017 flet) stay as planned.

## Goal

Every file of ClearMD reads in one sitting and holds one concern; every GUI has the same small,
template-aligned layout (ADR-0014's promise, made exact by ADR-0039). The owner's rule: **≤ 200
lines per file, a tolerance up to 250, not to be abused**.

## Scope

- **Includes:** every source file (frontend and backend) and every test file over the limit; the
  Qt draft of 016 moved to `frontend/pyside`; a test that enforces the rule; ADR-0039; one
  `README.md` per new folder.
- **Does not include:** any change of behaviour, output, wording or look; finishing feature 016
  (it continues after R01, in the new layout); dedupes and small improvements found on the way
  (listed in `plan.md`, phase P13, done after R01 one commit each).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_R01_modular_layout.py`) or a gate.

- [ ] **AC-01** No `.py` file under `src/`, `tests/` or `packaging/` is over 250 lines; at most
  10 % of them are over 200; no class is over 150 lines; no class mixes in another of ClearMD's.
- [ ] **AC-02** Each GUI (`ttk`, `pyside`, later `flet`) has the same folders: `app.py` (≤ 40 lines:
  build the window and run it), `window/`, `layout/`, `views/` (`dialogs/` inside), `components/`,
  `visuals/`; each layer imports only the ones below it; no GUI imports another or `backend.api`.
- [ ] **AC-03** A module under ~40 lines states in its docstring why it stands alone.
- [ ] **AC-04** Behaviour unchanged, proved at every step: the Markdown of every fixture (and,
  locally, of the private examples) byte-identical to the baseline; the ttk screenshots identical;
  the whole suite green; ruff, ruff format and mypy --strict clean.
- [ ] **AC-05** The executables still build and pass `check_executables.sh`; the ttk and CLI
  executables carry no other GUI toolkit.
- [ ] **AC-06** The entry points (`clearmd`, `clearmd-ttk`, `clearmd-pyside`) resolve.
- [ ] **AC-07** ADR-0039 accepted (it supersedes ADR-0014's layout section); a `README.md` in every
  folder.

## Plan

`plan.md`: the expert board's final plan (architect, two refactor experts, a QA strategist, a
manager, two auditors), approved by the owner on 2026-11-04 with the review by blocks.
