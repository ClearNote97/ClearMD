# Lessons learned for the ClearNote_Dev templates

What building ClearMD (features 001–015, refactor R01, 2026-10 → 2026-11) taught that a template should carry
from day one. Each lesson: what happened, then what the template should do. Ordered by how much it would have
saved.

## 1. Modularity is a rule the tests enforce, not a promise in an ADR

- **What happened.** ADR-0014 promised each GUI "the template's app/ views/ components/ layout/". Nobody checked
  it. Five weeks later `ttk/app.py` was one 447-line class, the presenter 724 lines and the PDF reader 1071.
  Undoing that took a 13-phase refactor (R01: 71 commits, 528 files).
- **For the template:**
  - Ship `tests/unit/test_module_size.py` and its helper `tests/support/source_tree.py` from the first commit.
    - The rule: ≤ 200 lines per file, 250 at most, and no more than 10 % of files above 200.
    - Classes ≤ 150 lines, no mixins of the project's own classes.
    - Every source module has a docstring.
    - A GUI's `app.py` stays ≤ 40 lines.
  - Ship `tests/unit/test_gui_layers.py`: inside a GUI, `app.py` → `window/` → `views/` → `components/` →
    `visuals/`, `layout/`, never upward; only `window/` knows the window class.
  - When the rule arrives late, use a **ratchet**. List what is over the rule today with its size. An entry may
    only shrink, and a stale one fails the test. It caught growth the same day, twice in R01.

## 2. The same skeleton in every interface

- One layout per GUI toolkit, with the same file and class names in each:
  - `app.py`: build the window and run it.
  - `window/`: the view the presenter draws on, plus small collaborators: dialog host, primary button,
    inputs/keyboard, pickers, closing, the toolkit's root.
  - `views/`: one step or dialog per file.
  - `components/`, `visuals/`, `layout/`.
- Everything every window decides the same way goes in the presenter package (`presenter/chrome/`): the
  header, the second button, the primary action's pause, the close policy. The tokens (palette, metrics,
  typography) go in `frontend/design/`. Without that, the second GUI (PySide6) copied ~200 lines of the first,
  line for line.
- The presenter is split too: a small facade over `session`, `display`, `background`, `intents/` (what the user
  does) and `screens/` (what each step shows).
- Converters that walk a tree share one shape: `writer/` with `state.py` and `dispatch.py`. The renderer class
  keeps only its recursive entry points.

## 3. Build the safety net before moving anything

A refactor is only as safe as the proof that nothing changed. R01's proof, all of which belongs in the template's
refactor playbook:

- **Golden outputs.** One SHA-256 per output file of every fixture corpus, in each mode
  (`tests/golden/manifest.txt` + `tests/support/golden.py`), compared by a test. Leave out anything with a date.
- **A private corpus** (real user documents, git-ignored) hashed the same way, as a *local-only* gate. It found
  nothing the fixtures missed, but it is the only proof on real documents.
- **Screenshots** of every screen, taken twice to prove they are deterministic, then compared byte for byte after
  every step.
- **The test-id multiset** (`function[params]`, without file paths), so splitting test files loses nothing.
- **Determinism first.** Run every artefact twice before trusting it as a baseline.
- **The baseline finds bugs.** It found a production bug: since 012, TeX and Excel failed whenever "images in a
  folder" was on. Every fixture was run in every mode, and nobody had done that before.

## 4. Two techniques, and only two

- **Module moves.** Bodies verbatim; only the import block changes, plus dropping a leading `_` when a name
  crosses a module. Verified by an AST comparison of every top-level definition.
- **Class decomposition.** Only `self.` changes to an explicit receiver. Watch for:
  - **Extra stack frames on recursive paths.** They change where depth limits trip. Pin those limits with a
    characterisation test first (R01 pinned 10 TeX nesting families).
  - **Shadowing.** Some names had to change beyond the `_` rule; say so in the commit.
- Never mix in dedupes, reordering, or "improvements". Note them for later instead.

## 5. Monkeypatching couples tests to module layout

- A patch on a module that no longer reads the name passes silently and tests nothing. Two rules:
  - **Patch where the name is read at call time.** Move the patch in the same commit as the code.
  - **Prove every seam.** Break it on purpose once, see the test fail, revert.
- Prefer injection (constructor parameters, `spawn=`, `clock=`) over patching module globals; the presenter had
  it and was the easiest piece to split.
- A meta-test that demanded *exactly one* acceptance file per feature blocked splitting `test_001`/`test_005`.
  Write meta-tests to accept the union of a feature's files.

## 6. Packaging leaks what the import graph allows

- `PyInstaller`'s `collect_submodules("pkg")` pulled the second GUI's toolkit (PySide6, +43 MB) into the first
  GUI's executable and the CLI.
- **For the template:**
  - Each executable filters the other interfaces out of its hidden imports and excludes their toolkits.
  - A test checks the spec does it.
  - The archive listing is diffed against an expected list at every phase.
- Heavy toolkits (Qt) go in an **optional extra**, not the base dependencies.
- PySide6 (LGPL) ships as a folder (onedir), not a single file.

## 7. Orchestrating agents

- **A board before a big change pays off.** Four independent surveys (architecture, two refactor areas, QA),
  then a manager's merged plan and two adversarial auditors. The auditors found real problems the plan had
  missed:
  - the red architecture test;
  - PySide6 leaking into both executables;
  - the `app.py` / `app/` name clash;
  - re-export shims meant to stay forever.
- **Delegate one phase per agent**, and give each a brief with:
  - the rules;
  - the exact gate commands, with exit codes checked (a gate piped into `tail` hid a red commit once);
  - a report file as the deliverable.

  The orchestrator re-runs the full gate itself before tagging.
- **Never run two gates at once on shared artefacts.** Two runs writing the same comparison file produced a false
  "differ".
- One shared brief file per phase group (`p10-brief.md`, `p12-brief.md`) kept four agents consistent.

## 8. Development environment and CI

- **The dev container needs every GUI toolkit's system libraries** (Qt: libEGL, libxkbcommon, libglib…), and
  so does CI. Add them with the toolkit, not when the first test fails.
- **Timing-based GUI tests are flaky under load** (a 0.05 s pump while PyInstaller builds). Pump until a
  condition holds, with a generous timeout.
- **Windows runners flake on Tk** (`couldn't read file focus.tcl`, earlier `msgcat`). Re-run once before
  debugging, and keep Tk setup explicit.
- **Pushing workflow files needs the `workflow` scope** on the `gh` token; ask for it early.
- **CI that runs only on `main`** needs `workflow_dispatch` to test a branch. Scripts that put
  `GITHUB_REF_NAME` in file names break on branch names with `/`.
- **`ruff format` also formats code blocks inside `.md` files.** Exclude contract files copied verbatim.

## 9. Releasing to non-technical users

- **Plan code signing at the start.** SignPath Foundation (free for OSS) requires:
  - a public repository;
  - a "Code signing policy" page with roles and a privacy statement;
  - product name and version inside the `.exe`;
  - uninstall instructions;
  - and above all **public reputation** (stars, forks, external mentions).

  ClearMD was refused for that last point. A template should ship the policy page, the version resource and
  the gated CI step, and the project should build visibility before applying.
- **When the user only tests executables,** every visible change needs screenshots in the repo and executables
  built and smoke-tested by CI (`--smoke`).

## 10. Process habits that worked

- **Spec-driven development**: an ADR per decision, a spec with numbered acceptance criteria, one acceptance test
  per criterion (checked by a meta-test), a review after each feature.
- **Supply chain**: exact pins for pre-1.0 libraries, and no release younger than two weeks (`uv` constraints).
- **Private examples**: a git-ignored folder used for local evaluation only, and a history scan before making
  the repository public.
- **Commits**: stage by path, never `git add -A`, so ignored and private files can never slip in.
