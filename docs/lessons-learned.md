# Lessons learned for the ClearNote_Dev templates

What building ClearMD taught that every ClearNote_Dev template should carry from day one. The period covered
is features 001–033, refactor R01 and versions 0.1.0 → 2.8.1 (2026-10 → 2026-11).

The lessons are grouped by theme:

| Part | Theme |
| --- | --- |
| I | Development philosophy |
| II | Architecture |
| III | Modularity |
| IV | Design and user experience |
| V | Interface text |
| VI | Quality and the safety net |
| VII | Operational efficiency: agents, environment, CI |
| VIII | Releasing to non-technical users |
| IX | What the audit boards taught (2026-11-08) |
| X | Applying an audit (2.9.0 – 2.10.0) |
| XI | What the second audit taught (2026-11-09) |
| XII | Applying the second audit (2.11.0) |
| XIII | What the third audit taught (2026-11-09) |
| XIV | Applying the third audit (2.12.0) |
| XV | What the fourth audit taught (2026-11-09) |

Each lesson says what happened, then what a template should do. Within a part, the lessons that would have
saved the most come first.

> **Revision history.** On 2026-11-08 this file was rewritten twice:
>
> - before the external audit by three boards (backend, frontend, conciliator), to bring Parts I–VIII up to
>   2.8.1;
> - after the audit, to add Part IX.
>
> On 2026-11-09, after the audit's improvements (2.9.0 and 2.10.0), Part X was added before the
> second audit, and Part XI after it.
>
> The full report is in [`audit/2026-11-08-audit-boards.md`](./audit/2026-11-08-audit-boards.md).

---

## Part I — Development philosophy

### I.1 "Clarity is care" is a design rule, not a slogan

- **What happened.** The primary user is someone who has never opened a terminal (ADR-0013). Every time a
  choice traded power for simplicity and simplicity won, the user approved it at once. The decisions that
  needed rework were the ones where the app asked something it could have decided by itself. For example,
  "keep the files?" was asked on two different paths until feature 033 merged them into one place.
- **For the template:** write the persona into the constitution, and add one review question to every
  feature: *what does this ask the user that we could decide for them?* Power belongs in CLI flags. A GUI
  asks only what the user alone can answer.

### I.2 Never a control without an action

- Checkboxes for splitting large files were removed until Split existed (feature 024). A control that does
  nothing teaches the user that controls lie.
- **For the template:** a feature may not add a visible control before the behaviour behind it exists.

### I.3 Symmetry is a feature the user notices

- The user compared the three windows side by side and spotted every difference: tile centring in flet, a
  disabled arrow that looked enabled, a missing "Go Back Home".
- **For the template:** when one product has several interfaces, one presenter decides *what* is shown. A
  per-interface test then checks each window draws exactly that. A lead referees layout disagreements and
  sends the winning choice to every window.

### I.4 Measure before building the "maybe"

- The roadmap's second queue lane was dropped after one real run showed light files never wait (ADR-0050).
- **For the template:** a roadmap item that rests on a performance guess must first get a measurement.

### I.5 Ask a council when the user is the unknown

- "How big is a part that fits an AI?" had no technical answer. Seven deliberating roles turned it into one
  radio and one number, labelled as approximate, and recorded the dissent.
- **For the template:** use a deliberative council for questions about *people*. Questions about code don't
  need one. Always record the minority view.

### I.6 Review after every stage

- "Proceed" authorised only the stage proposed. Stopping to review after each feature caught requests the
  spec had not imagined: Merge's ▲ ▼ order, "Go Back Home" in the results, and one redesigned "What Next?"
  menu.
- **For the template:** the agent contract should say that approval covers one stage. Long autonomous runs
  must be authorised explicitly and must end at a stated milestone.

---

## Part II — Architecture

### II.1 Core and adapters, with one presenter for every window

- The backend (`backend/api`) knows nothing about windows. The presenter (`frontend/presenter`) decides
  state, texts and which controls exist. Each toolkit (ttk, PySide6, flet) only draws. This split is what
  made a third GUI cost weeks instead of months.
- **For the template:** ship the presenter skeleton with these parts:
  - a facade over `session`;
  - `display` and `background`;
  - `intents/`, for what the user does;
  - `screens/`, for what each step shows;
  - `chrome/`, for what every window decides the same way.

  Add a fake view for tests from the first commit.

### II.2 The presenter says which controls exist, not only what they say

- Merge's ▲ ▼ are flags on each input row (`InputRow.up`, `InputRow.down`). They are set only for Merge,
  and only where the move is possible. No window decides by itself that the first row cannot go up. The
  same goes for "What Next?": `next_choices()` returns the tiles in order, with the current tool first.
- **For the template:** put a rule in the view model whenever two windows could get it wrong in different
  ways. The windows render data, never policy.

### II.3 Add a tool as a mode of the same batch, not as a new pipeline

- Split and Merge are a field on the plan (`SplitSpec`, `MergeSpec`). Planning, the queue, cancelling, the
  "already exists" rule, the summary and the history stayed one piece of code. Each tool cost a few small
  modules, not a second app.
- **For the template:** when a product grows new verbs, extend the plan's data before adding new flows.

### II.4 Let the words follow the tool through the catalog

- `Catalog.for_tool("split")` lays Split's texts over Convert's keys (`[tool.split]`). Every view kept its
  keys, and the three windows changed their words with no code of their own.
- Overlays are also a cost. In feature 033, several per-tool overlays of the same title had to be removed
  once the title became the same for every tool.
- **For the template:** ship layered catalogs. Review the overlays whenever a text becomes universal.

### II.5 Share design data as data: tokens, and even icons

- Palettes, metrics and typography live in `frontend/design/` as plain data. In feature 033 the tool icons
  joined them: `design/tool_art.py` holds each icon's geometry once. Each toolkit only renders it (Tk
  images, Qt painter, flet SVG).
- **For the template:** keep a toolkit-free `design/` package with tokens and icon geometry, and test that it
  imports no toolkit.

### II.6 Heavy work in a separate process

- Converting in a worker process (ADR-0015) kept every window responsive. Windows' EcoQoS throttling of
  background processes was found only on a real machine and fixed in 1.0.1.
- **For the template:** long work never runs in the GUI process. Test on the user's operating system before
  calling performance done.

---

## Part III — Modularity

### III.1 Modularity is a rule the tests enforce, not a promise in an ADR

- **What happened.** ADR-0014 promised each GUI "the template's app/ views/ components/ layout/". Nobody
  checked it. Five weeks later:
  - `ttk/app.py` was one 447-line class;
  - the presenter was 724 lines;
  - the PDF reader was 1,071 lines.

  Undoing that took a 13-phase refactor (R01: 71 commits, 528 files).
- **For the template:**
  - Ship `tests/unit/test_module_size.py` and `tests/support/source_tree.py` from the first commit:
    - at most 200 lines per file, 250 at most, and no more than 10 % of files over 200;
    - at most 150 lines per class, and no mixins of the project's own classes;
    - a docstring in every module;
    - at most 40 lines in a GUI's `app.py`.
  - Ship `tests/unit/test_gui_layers.py`. Inside a GUI, imports go one way only: `app.py` → `window/` →
    `views/` → `components/` → `visuals/` and `layout/`. Only `window/` knows the window class.
  - When the rule arrives late, use a **ratchet**:
    - list what breaks the rule today, with its size;
    - an entry may only shrink;
    - a stale entry fails the test.

    It caught growth the same day, twice.

### III.2 Size limits shape the design, and that is good

- In feature 033 the presenter class reached 161 lines, over the limit. The fix was not trimming. "What
  next?" moved into the `Navigation` collaborator it belonged to, and an old entry point
  (`Presenter.convert_more`) disappeared.
- **For the template:** treat a size failure as a signal that a collaborator is missing. Don't squeeze the
  code to fit.

### III.3 The same skeleton in every interface

- Each GUI toolkit has one layout, with the same file and class names in each:

  | Folder | Holds |
  | --- | --- |
  | `app.py` | build the window and run it |
  | `window/` | the view the presenter draws on, plus small collaborators: dialog host, primary button, keyboard, pickers, closing |
  | `views/` | one step or dialog per file (for example `views/dialogs/what_next.py` in all three) |
  | `components/`, `visuals/`, `layout/` | the pieces the views are built from |

- Without that, the second GUI copied about 200 lines of the first, line for line.
- **For the template:** ship the GUI skeleton with its layer test.

### III.4 Two refactoring techniques, and only two

- **Module moves.** Bodies stay verbatim; only the import block changes, plus dropping a leading `_` when a
  name crosses a module. An AST comparison of every top-level definition verifies it.
- **Class decomposition.** Only `self.` changes, to an explicit receiver. Watch for:
  - **Extra stack frames on recursive paths.** They change where depth limits trip. Pin those limits with a
    characterisation test first.
  - **Shadowing.** Some names had to change beyond the `_` rule. Say so in the commit.
- Never mix in dedupes, reordering or "improvements". Write them down for later.

### III.5 Converters that walk a tree share one shape

- Each one has a `writer/` with `state.py` and `dispatch.py`. The renderer class keeps only its recursive
  entry points.

---

## Part IV — Design and user experience

### IV.1 One decision, one place

- **What happened.** After a run, "Convert more" asked "keep the files?". Later "Go Back Home" was added,
  and it would have asked the same question again. Feature 033 replaced both with one "What Next?" dialog:
  - three small tool tiles, with the tool just used first ("Convert Again");
  - one box, "Keep the files you chose", ticked by default;
  - Cancel.
- **For the template:** when a new path would repeat a question, redesign the menu so the question is asked
  once, next to the choices it affects. Name destinations ("Split"), not answers ("Yes").

### IV.2 When a toolkit lacks a feature, redesign the space it leaves

- flet 1.0 cannot receive files dropped from the system. An empty list that said "use the buttons" was dead
  space. Two large tiles, each with an icon, a title and what it takes, became the way in and turned the
  gap into the first step.

### IV.3 Disabled must look disabled, in every toolkit

- flet keeps an explicit `icon_color` even when a button is disabled. The first-row ▲ looked clickable.
  The fix makes the colour follow the state. A test now compares the colours of an enabled arrow and a
  disabled one.
- **For the template:** every toolkit adapter sets state-dependent colours explicitly, and a test asserts
  the difference.

### IV.4 A reference size referees layout

- When two windows disagreed on a layout, the lead picked the one that kept the file list visible at
  1080×720 and sent it to all three. Later, 800 px and Spanish texts (longer than English) found the last
  clipped labels.
- **For the template:** fix a minimum window size and the longest language as test inputs from the start.

### IV.5 Look at every screenshot, not only the tests

- A CI shot showed Split's page under the name "Merge". In feature 033 another showed flet's tile icons
  stuck to the top edge. The tests could see neither.
- **For the template:** have CI take a screenshot of every screen, in both themes and both languages. A
  human or an agent looks at them before every release.

---

## Part V — Interface text

### V.1 Fix the capitalisation rule on day one, and test it

- ClearMD moved to Title Case at 1.2.0, and most of the catalog's titles and buttons had to be rewritten.
  A test now checks every title, button and summary heading, in both languages, against a list of lowercase
  connectors. Options and explanations stay in sentence case.
- **One text rule covers every surface:** window titles, buttons and generated documents (the summary in
  Markdown and PDF).

### V.2 Tests read strings from the catalog, never copies of them

- Dozens of tests had copies of catalog text, so every wording change broke them. A `text(key)` helper ends
  that.
- When a text gains a placeholder (`"{tool} Again"`), every test that formats texts generically has to know
  it. In feature 033 one such test failed with `KeyError: 'tool'`.

### V.3 The welcome must describe the whole product

- After Split and Merge arrived, the welcome still talked only about converting. In feature 032 it was
  rewritten: "Convert, split or merge your documents in three steps".
- **For the template:** when a feature adds a verb, its spec lists the first-run texts to update.

---

## Part VI — Quality and the safety net

### VI.1 Build the safety net before moving anything

- **Golden outputs.** Store one SHA-256 per output file of every fixture corpus, in each mode, and compare
  them in a test. Leave out anything with a date.
- **A private corpus** of real user documents, git-ignored, hashed the same way, used as a local-only gate.
- **Screenshots** of every screen, taken twice to prove they are deterministic, then compared byte for byte
  after every step.
- **The set of test ids** (function and parameters, without file paths), so splitting test files loses
  nothing.
- **Determinism first.** Run every artefact twice before trusting it as a baseline.
- **The baseline finds bugs.** Running every fixture in every mode found a production bug: TeX and Excel
  had been failing whenever "images in a folder" was on.

### VI.2 Monkeypatching couples tests to module layout

- **Patch where the name is read at call time,** and move the patch in the same commit as the code.
- **Prove every seam.** Break it on purpose once, watch the test fail, then revert.
- Prefer injection (constructor parameters, `spawn=`, `clock=`) over patching module globals.

### VI.3 Meta-tests: write them to accept unions and read exact names

- A meta-test that demanded *exactly one* acceptance file per feature blocked splitting test files. Accept
  the union of a feature's files.
- The acceptance meta-test reads criterion numbers with `ac_(\d+)`. A test named `test_ac_02_and_03`
  covers only 02. Use one name per criterion.
- When a later feature changes an earlier criterion, mark it "Amended by feature NNN" in the old spec and
  keep its test green. Don't delete it.

### VI.4 Give a new enum value a sweep

- Adding `FormatId.MARKDOWN` (split-only) broke every test that assumed "every format converts". A named set
  (`CONVERTIBLE`) says what the code means.

### VI.5 Type checkers protect state machines, and need help with them

- `mypy --strict` flagged `presenter.state is AppState.READY` right after a call that changed the state. It
  had narrowed the type earlier. `state in (AppState.READY,)` states the intent and passes.

---

## Part VII — Operational efficiency: agents, environment, CI

### VII.1 Orchestrating agents

- **A board before a big change pays off.** For R01, four independent surveys were followed by a merged plan
  and two adversarial auditors. The auditors found real problems the plan had missed: a red architecture
  test, PySide6 leaking into both executables, a name clash, and shims meant to stay forever.
- **One presenter contract, three toolkit agents, one lead.** The lead owns the backend, the presenter and
  the catalogs. Each toolkit agent owns its folder and its tests, nothing else, and never commits. It writes
  a report file that the lead reads.
- **Each brief carries:**
  - the rules;
  - the exact gate commands, with exit codes checked (once, a gate piped into `tail` hid a red commit);
  - a report file as the deliverable.

  The lead re-runs the full gate before tagging.
- **Never run two gates at once on shared artefacts.**

### VII.2 Development environment

- **The dev container needs every GUI toolkit's system libraries**, and so does CI. Add them with the
  toolkit.
- **Installing system packages to measure something pollutes the container.** GTK brought in a text-shaping
  library that changed Pillow's rendering and broke byte-for-byte asset tests. Measure in a separate
  container.
- **Keep the installed version fresh.** After every version bump, run `uv lock` and `uv sync`. Do it after
  the gate run, never during it. Screenshots read the installed package's version.

### VII.3 CI

- **Timing-based GUI tests are flaky under load.** Pump until a condition holds, with a generous timeout.
- **Windows runners need the window focused** before sending keys, and Tk occasionally fails to load
  its own files. Re-run once before debugging.
- **Fonts differ between runners.** A test at 800 px that asserted how text wrapped failed on Ubuntu.
  Assert the layout (what is visible, what fits), not the font's wrapping.
- **Run the full matrix on the branch before tagging.** After 2.8.0, three Windows/Ubuntu test-only failures
  surfaced on `main`. Users were not affected, but `workflow_dispatch` on the branch would have caught them
  first.
- **Pushing workflow files needs the `workflow` scope** on the `gh` token.
- **`ruff format` also formats code blocks inside `.md` files.** Exclude contract files that are copied
  verbatim.
- **Check a CI step that depends on how the environment looks** (a compiler banner, an exe's version) in a
  manual run before tagging.

### VII.4 Branch hygiene

- **After each release, delete merged branches**, and tag release branches before deleting them. At 2.8.0,
  25 stale remote branches were removed and only `main` was kept.

---

## Part VIII — Releasing to non-technical users

### VIII.1 Ship what the user can actually test

- The user tests only packaged executables. So every visible change needs:
  - screenshots in the repository;
  - executables that CI builds and smoke-tests (`--smoke`);
  - a release they can download.

  A feature isn't done until it is released.

### VIII.2 Plan code signing at the start

- SignPath Foundation (free for open source) requires:
  - a public repository;
  - a code-signing policy page;
  - the product name and version inside the `.exe`;
  - uninstall instructions;
  - above all, **public reputation**.

  ClearMD was refused on that last point. Ship the policy page, the version resource and the gated CI step,
  and build visibility before applying.

### VIII.3 Packaging leaks what the import graph allows

- `collect_submodules("pkg")` pulled PySide6 (+43 MB) into the other executables. Each executable must
  filter out the other interfaces, and a test checks the build spec. Heavy toolkits go in optional extras,
  and LGPL Qt ships as a folder.

### VIII.4 Public files and checksums from the first public commit

- These files are cheap to write, and they are what visitors and signing programmes look for:
  - `SECURITY.md`;
  - `CONTRIBUTING.md`;
  - `CODE_OF_CONDUCT.md`;
  - issue forms;
  - `CHANGELOG.md`;
  - `CITATION.cff`, kept on the project's version by a test.
- One `SHA256SUMS.txt` per release lets anyone check a download while the executables are unsigned. Write
  it outside the folder being hashed.
- PyPI: a checked build on every tag, with Trusted Publishing prepared but off until the owner enables it.

### VIII.5 Supply chain and privacy

- Use exact pins for pre-1.0 libraries, and accept no release younger than two weeks.
- Private examples go in a git-ignored folder. Scan the history before making a repository public.
- Stage by path, never `git add -A`.

---

## Part IX — What the audit boards taught (2026-11-08)

Two boards audited 2.8.1, each with four lenses: logic, efficiency, what the user sees, and "Clarity is care".
They reviewed independently, then debated each other's reports. A conciliator verified the result against the
code: of 38 merged findings, 29 were confirmed, 9 were partly true, and none was refuted. Score: 6.5 of 10. The
core lesson is that the happy path was well protected, and trust broke at the edges.

### Philosophy

#### IX.1 Trust breaks where the user cannot check

- **What happened.** The worst findings were not crashes. They were results reported as fine when they were
  not:
  - a re-split deleted the earlier parts before it had the new ones;
  - two merges in the same minute overwrote each other;
  - images broke when Markdown was split or merged;
  - a semicolon CSV (Excel's default in Spanish) came out as one column;
  - a folder plus one of its own files was processed twice.

  The opposite failure did as much damage. Warnings appeared where nothing was wrong: almost every PDF carried
  a ⚠️ for a clean-up that was good news.
- **For the template:** every feature spec gets an "honesty" section with two lists. First, what the user
  cannot verify themselves. Second, how the product proves it, or how it says that it can't.

#### IX.2 A message never guesses a cause the code did not check

- These messages each named a cause that had not been checked:
  - a password-protected Word file was called "damaged";
  - an empty text file was called "a scanned PDF";
  - a failed merge asked "is the disk full?".

  Users follow a wrong hint to the letter, so it is worse than a vague one.
- **For the template:** each error code means exactly one thing. Ship end-to-end "sad path" tests for every
  tool: a damaged file, an empty file, an encrypted file, and a cancel halfway.

### Architecture and logic

#### IX.3 Replacing a set of files must be atomic as a set

- Atomic single-file writes were already solid. The gap was sets: split parts, image folders. Write the new
  set aside, move it in at the end, and only then delete the old one.
- **For the template:** ship a test that cancelling halfway keeps the earlier result.

#### IX.4 Generated names need a collision suffix

- A name built from a minute-precision timestamp collides. Add `(2)`, `(3)`, and test "two runs in a row".

#### IX.5 Deduplicate inputs by real file, after expanding folders, in the backend

- Do it in the backend, so every interface gets it.

#### IX.6 Anything that moves or combines Markdown checks its local links

- Every image or local link in the result must point to a file that exists.

#### IX.7 Notes have two levels from day one

- The two levels are *information* and *attention*. What the user decided (for example "keep") never counts as
  a problem, in the window or in the report.

### Design and interface text

#### IX.8 Grow the texts with the product

- The app went from one tool to three faster than its texts did:
  - Help described a path that no longer existed;
  - the welcome promised "three steps" where there were four;
  - the CLI said "nothing to convert" for a merge.
- **For the template:** test the Help. Each button it names must exist, and each tool on Home must have a
  section. When a feature renames or adds a button, search the catalog for every sentence that names it.

#### IX.9 Window text and terminal text are separate channels

- The window showed `--overwrite` and a library's name, and the terminal said "choose *Into N parts*".
- **For the template:** keep separate catalog branches for the window and the terminal. Add a linter that
  bans the following from window text:
  - `--options`;
  - library names;
  - exception names.

  The same linter requires singular and plural forms next to every number.

#### IX.10 The last screen says where the result is, in words

- Show the exact path as text. No explanatory text may be truncated unless the user has a way to read it in
  full that does not need a mouse.

#### IX.11 Lists have a budget test

- Every list in an interface gets a test with 1,000 rows, and a test that the scroll bar is visible at the
  minimum window size. Per-row images are cached.

#### IX.12 Contrast claims need a test

- An ADR stated "every pair passes AA", but derived colours fell below 4.5:1. Compute the ratios in a test,
  for both themes.

### Operations and release

#### IX.13 The default download weighs what the default install installs

- The installer was about 176 MB for a default install of about 37 MB. Put a size budget on every published
  file in CI.

#### IX.14 The first run speaks the installer's language

- The installer was in Spanish, and the app opened in English (ADR-0017). Pass the installer's choice to the
  first-run settings.

#### IX.15 Fixtures carry the public's real formats

- Include files as people really have them:
  - CSV with `;`, a BOM, and cp1252 encoding;
  - old Office files (`.doc`, `.xls`, `.ppt`), each with its own message;
  - folders of numbered chapters, sorted in natural order (1, 2 … 10).

### Running audit boards

#### IX.16 Independent first, then debate, then a verifier

- **Debate added real value.** It merged duplicates across boards, and it traced several findings to one root
  cause, for example "never destroy earlier work before the replacement exists".
- **Debate also amplified by echo.** "Four auditors found it" raised severities without a new check. A false
  claim spread that way: that kept results left a run "finished with problems". Only the conciliator's own
  check against the code stopped it.
- **For the template:**
  - Agreement confirms a fact, not its severity. A claim adopted from another auditor is re-checked in the
    code before its severity is raised.
  - Auditors read the ADRs before recommending something that contradicts one, and cite the ADR when they do.
    No board noticed that "follow the system language" contradicts ADR-0017.
  - The debate round diffs against round 1, so that real findings are not dropped. Here it dropped the old
    Office formats and the startup language. The conciliator restored them.
  - Each auditor gets its brief, a schema, a retry on network failure and a report as the deliverable. A first
    run lost 6 of 9 agents to a DNS outage. With a retry per agent, the rerun lost none.
  - Keep the private corpus out of reports. Auditors were told not to quote private documents, yet two file
    names still leaked into evidence strings. Scan the report before publishing it.

---

## Part X — Applying an audit (2.9.0 – 2.10.0)

The owner accepted the ten improvements and three decisions. The lead did the backend, the
presenter and the texts. Three toolkit agents did the windows, and a doubts board settled the
questions about people. Lessons from turning findings into releases:

### X.1 Plan releases by the files that features share, not by the findings' numbers

- **What happened.** The plan was three releases (improvements 1–3, 4–7, 8–10). Features 035,
  036 and 037 all changed the two catalogs and the installer script. Splitting them by hand,
  with no local Windows to test the installer, was riskier than shipping them together.
  2.10.0 carries all three. The doubts board's real safeguard was kept: a full manual release
  run on the branch before the tag.
- **For the template:** split the text catalogs by area (`i18n/<lang>/<area>.toml`), so that two
  features rarely touch the same file. When a release must carry less than the working tree
  holds, commit through a temporary index (`GIT_INDEX_FILE`). The agents keep working in the
  tree, and the branch's CI (`workflow_dispatch`) tests exactly what will be tagged.

### X.2 A rule moved into the presenter breaks fakes that encoded the old world

- Merge now needs two documents before it starts. Two ttk tests used the fake backend's default
  plan, which had one document, and failed only on CI. A fake's defaults are assumptions:
  tests that depend on a rule should pass their data explicitly.

### X.3 Copies of interface text in tests still break

- Three tests broke again when the texts were made honest: "possible zip bomb", "exceeded the
  time limit", "every N pages". Lesson V.2 stands, and a template should enforce it with a meta
  test that bans literal catalog sentences in test files.

### X.4 Ask a board when the question is about people, then record the deviation

- Three doubts went to a small board, each a choice a user would feel: a light installer, the
  windows' names, and what an unexpected error shows. The board gave exact strings, risks,
  checks and its dissent. The lead followed it, except on how to group the releases, and wrote
  that down (`docs/audit/2026-11-09-doubts-board-1.md`).

### X.5 Give agents a measurable budget

- The ttk agent was asked for "1,000 rows without freezing". It measured 4.56 s, cached the row
  pictures and drew only visible rows, and reached 0.05 s. A theme switch went from 7.98 s to
  0.53 s. A number in the brief turned a vague wish into a test.

### X.6 Patterns worth keeping

- **Time limits count from the last progress, under a ceiling.** A long file that keeps moving
  finishes, and a stuck one stops. The window can say "page N of M".
- **Anything sent to a public page is cleaned first.** "Copy Details" replaces every path with
  `<file>.ext`, because issues are public and paths carry people's names.
- **Some toolkits cannot confirm success.** flet's clipboard is asynchronous: a failure inside it
  never reaches the presenter. Write the limit down rather than promise "Copied" without it.
- **Regenerate screenshots after the version bump.** The windows' shots showed the old version
  until they were taken again (lesson VII.2, met again).

---

## Part XI — What the second audit taught (2026-11-09)

The second audit used new agents from scratch, with Part IX's rules built in, on version 2.10.0.
The score went from 6.5 to 7 out of 10. Of the first audit's ten recommendations, five were
fully resolved and five partly, and none got worse. The conciliator verified 27 findings: 21
were confirmed, 6 partly true, and none was refuted. Report:
[`audit/2026-11-09-audit-boards-v2.md`](./audit/2026-11-09-audit-boards-v2.md).

### Product

#### XI.1 After "never lose work" comes "never say something false"

- **What happened.** The second audit found results reported as fine that were not:
  - a Windows-encoded (cp1252) text came out with "ańo", with no note;
  - "split into 3 parts" could give one part;
  - "Copy Details" let a quoted file name through;
  - an empty PDF was called "damaged";
  - cancelling during Merge's last step showed an "unexpected error".
- **For the template:**
  - Every promise written in an ADR or in a message gets a fixed test with its hard case. A
    promise like "a cell is a cell", "we hide your names" or "nothing is written yet" needs one.
  - If the code cannot guarantee a promise, the text says "we try".
  - Whatever is rebuilt by a heuristic, or not delivered as asked, is said in the summary.

#### XI.2 One text decoder for the whole product

- Split decoded cp1252 correctly and Convert did not: two paths, two answers for one file.
- **For the template:** one decoder, and a cp1252 file with ñ and accents in the fixtures.

#### XI.3 Cancelling is never an error, at any stage

- Add a test that cancels at each long stage, the final write included.

#### XI.4 Output names depend only on the original

- They must never depend on the language or on the batch. Rules per tool live in the backend,
  so the command line and the windows agree. Images were fixed for the windows but not for the
  command line.

#### XI.5 Estimates calibrated on synthetic data must be revalidated on real documents

- Do it before a calibrated estimate is allowed to leave a file out. PDFs are better estimated
  by pages than by bytes.

### Applying an audit

#### XI.6 Verify each recommendation after applying it

- A short pass afterwards that marks each recommendation resolved, partly done or pending
  would have caught the half-done ones: Merge and images in the command line, the empty file.
- Prefer corrections of truth over new controls. Each confirmation, undo or extra option must
  justify itself against "Clarity is care".

### Operations

#### XI.7 Profile CI before parallelising it

- A `gc.collect()` after every test made the suite about 3.5 times slower than needed: 600
  catalog tests took 27.4 s with it and 7.7 s without.
- **For the template:** an autouse fixture with a global cost lives only in the folder that
  needs it. Upload the JUnit report so the slow tests are visible.

#### XI.8 With an installer, install the app as a folder, and measure the time to the window

- A one-file executable unpacks itself on every start (about 5 s on Windows).
- **For the template:** with an installer, ship the installed copy in folder mode. Measure the
  time from launch to the window in CI.

### Running audit boards (second time)

#### XI.9 The rules worked; tighten the ones that leaked

- Reading the ADRs, the `reverified` flag and the round-to-round comparison all worked: no real
  finding disappeared, and the debate fixed a wrongly attributed cause with a new measurement.
- Some severities still rose without being re-verified.
- **For the template:**
  - Require `reverified=true` to raise a severity.
  - Forbid merges that raise a severity without new evidence.

#### XI.10 The conciliator reproduces the top findings and answers the owner's question

- Running the three most valuable findings and the measurement that answered the owner's
  question ("is this slowness normal?") took minutes and gave certainty.
- **For the template:** make both part of the conciliator's brief.

---

## Part XII — Applying the second audit (2.11.0)

The owner accepted the ten improvements of the second audit and the conciliator's answers to its
disagreements. Written before the third audit.

### XII.1 When a promise fails, fix the code and soften the text

- "Copy Details" promised to hide file names and did not always do it. The code now hides more:
  quoted names, the names of the chosen files, and folders with spaces. The text now promises
  less: "we tried to hide them; check before you send it".
- **For the template:** a privacy or safety promise in the interface is worded as an effort, and
  a test feeds it the hard cases.

### XII.2 One fragment, many messages

- How to report a problem was said in four places, each a little differently. One catalog entry
  (`report.how`) is now inserted wherever a message names it (`{report}`).
- **For the template:** shared sentences live once in the catalog, and the catalog fills them in.

### XII.3 A test can enshrine a bug against its own ADR

- A table test asserted that a cell wrapped over three lines made three rows. That is exactly
  what ADR-0034 forbids. The test was amended to say what the ADR promises, and a second test now
  keeps a grouped first column as rows of their own.
- **For the template:** when a fix breaks an old test, read the test against the spec before
  "fixing" the code back.

### XII.4 Architecture first, then recalibrate, and write down the limit

- Estimating PDFs by pages would have loaded PDFium in the windows, against ADR-0015 and against
  the start-up improvement of the same round. The estimates were recalibrated with real
  measurements instead, and the limitation is written down.
- **For the template:** when two improvements pull apart, keep the architectural rule and record
  the trade-off.

### XII.5 Lazy imports need a test, and a profile

- The windows were loading PDFium and openpyxl through a chain of five imports. Moving two
  imports into functions removed them all, and the command line now starts in 0.40 s instead of
  0.56 s. A test now checks, for every interface, that no converter library is loaded at start.
- **For the template:** profile once (`-X importtime`), then guard the result with a test.

### XII.6 A one-file and a folder build from one analysis

- PyInstaller can build both the portable one-file app and the installer's folder from one
  analysis. In the folder copy the splash module exists but is not initialised, so the launcher
  must check `is_alive()`.
- **For the template:** build in the dev container before trusting CI with a packaging change.
  The first local build caught the splash crash in minutes.

### XII.7 Toolkit agents see presenter gaps

- The flet agent noticed that after an unexpected error the Results page did not write where the
  folders were: the presenter had not told it. The fix took one line.
- **For the template:** ask toolkit agents to report observations outside their area, even when
  their own part is done.

### XII.8 Partial is said as partial

- Some recommendations were done only in part:
  - result names that depend on the batch;
  - a note on rebuilt equations (incoherent ones are now kept as text);
  - PDF estimates by pages (recalibrated instead).
- They are listed as such for the third audit to check, never reported as done.

### XII.9 A layout test only counts on the platform with the widest font

- The Qt test that the longer "Process Summary" label is whole passed in the Linux container and
  failed in CI on Windows, whose fonts are wider. The fix let the label keep its natural width
  and let its choices wrap instead.
- **For the template:** a "nothing is cut" test runs on Windows in CI before a release, and
  locally it is checked with a font larger than the target's.

## Part XIII — What the third audit taught (2026-11-09)

The third audit used new agents from scratch on version 2.11.0. Each board had five experts,
four of them looking from angles not used before: security and privacy, fidelity of the content
for an AI, accessibility, and first use and installation. "Claridad es cariño" stayed on both
boards. Three conciliators worked in a chain, all bound by "Claridad es cariño": truth (verify
and reproduce), value for the person, and doctrine with a plain synthesis. The score stayed at
7 out of 10 because the look went deeper, not because the product got worse. Of the second
audit's ten recommendations, two were fully resolved and eight partly; none got worse. The
conciliators verified 78 findings: 61 confirmed, 17 partly true, none refuted. Report:
[`audit/2026-11-09-audit-boards-v3.md`](./audit/2026-11-09-audit-boards-v3.md).

### Product

#### XIII.1 A fix is only done when its test uses the hard case

- **What happened.** Release 2.11 added a test for Windows-encoded text and the improvement was
  counted as done. The test used a long sentence, which the decoder happens to guess right. A
  short note in cp1252 ("Canción, mañana") still comes out as "Canci¾n, ma±ana", and a short CSV
  of names can come out in Korean characters.
- **For the template:**
  - Before calling a fix done, ask: "would this test fail with the old code, and with a shorter
    or harder input?"
  - For text, the fixtures are one-line files in cp1252 with accents in each target language.

#### XIII.2 A change that people can see updates every text that describes it

- ADR-0053 installed the Classic App as a folder. The installer still called it "one file that
  unpacks", and the download page still said "to uninstall, delete the file". Four auditors found
  the same stale sentence.
- **For the template:** every ADR that changes packaging, start-up or installation lists, under
  Consequences, "review the installer's texts, the release notes and the README", and a test
  forbids the old sentences.

#### XIII.3 For an AI tool, the output promise is enforced in one place

- An email or a web page converted by a third-party converter can keep remote images (a read
  receipt for the sender) and raw HTML, against "everything stays on your computer".
- **For the template:** one common pass after every converter, ours or not, enforces what the
  output may contain (no remote images, no raw HTML, notes kept), with one test over every
  format.

#### XIII.4 A warning uses the same rule that acts

- A large PDF was warned "may take more than 10 minutes and stop", while the real stop rule (no
  progress) lets it finish in about 2. The warning pushed people to Split, which cleared the rest
  of their list.
- **For the template:** a warning is computed from the rule that actually stops the work. A
  report after an error never shows "0" for things that were done.

#### XIII.5 "All or nothing" must not throw away good work

- Split stages its parts and keeps the old ones until the new ones exist (from the first audit).
  But if one part stops, every good part is discarded, and the empty folder then counts as "an
  existing result".
- **For the template:** separate "never destroy the old result before the new one exists" from
  "keep whatever new work succeeded". An empty folder is never a result.

#### XIII.6 Accessibility depends on which file is downloaded

- A screen reader cannot read the Classic App, which is the only one in the light installer. The
  advice "use the Qt app" did not say which installer brings it.
- **For the template:** with several editions, the accessibility note names the file to
  download.

### Running an audit

#### XIII.7 Five experts per board give depth, and duplicates

- New lenses found what the old ones could not: remote images in the output, the screen-reader
  gap, fidelity measured on real tables. They also repeated each other: four auditors found the
  installer's sentence.
- **For the template:** keep the rule "agreement confirms the fact, it does not raise the
  severity"; it worked.

#### XIII.8 Three conciliators with separate roles, the last one for doctrine

- Truth reproduced the most important failure itself. Value ranked by what a person feels.
  Doctrine caught two recommendations of the first two that went against decisions the owner had
  already taken (keeping the worker alive between tasks, confirming every Cancel), and corrected
  a third (the screen-reader line must point to the full installer).
- **For the template:** keep a doctrine conciliator with access to the earlier audits. Pass the
  owner's "do not do" decisions to every board and conciliator as explicit constraints, or they
  come back.

#### XIII.9 A merge between two auditors is confirmed by the receiver

- Comparing what was dropped between rounds found a real loss: a keyboard shortcut (Ctrl+0) that
  each auditor thought the other kept.
- **For the template:** when two auditors merge findings, the one who receives it confirms it,
  not the one who gives it up.

#### XIII.10 A finding measured on a private document needs a public twin

- Some measurements used the owner's private documents. They cannot become fixed tests.
- **For the template:** each such finding gets a public or synthetic equivalent before it turns
  into a test.

#### XIII.11 "Claridad es cariño" binds the conciliators too

- The owner asked that the conciliators also write with care. Their synthesis came out in short
  paragraphs, with what improved, what is still not true and what to decide, in plain words.
- **For the template:** the reader of an audit is a person; the rule that governs the product
  governs the report about it.

## Part XIV — Applying the third audit (2.12.0)

The owner accepted the ten improvements and decided the five open questions (article mode by
default, the empty file stays "failed", a report channel without an account, signed installers,
an ADR on hidden PDF text). Written before the fourth audit.

### XIV.1 Try the most likely encoding first, and keep it only if it reads well

- A general detector scores short texts badly. Trying Windows' Western encoding first, and keeping
  it only when every character beyond ASCII is a Western letter or mark and most letters are ASCII,
  fixed every one-line case while Cyrillic and Japanese are still detected.
- **For the template:** for a known audience, a cheap plausibility check before the general
  detector; the fixtures are the shortest real inputs, in each language.

### XIV.2 An output guarantee belongs where every converter's result passes

- The pass that turns remote images, unsafe links and active HTML into text sits in the worker,
  after every converter. One place covered markdown, a third party's, and ours.
- **For the template:** find the one choke point every result crosses; enforce the promise there,
  with a note, and test it with a hostile fixture per format.

### XIV.3 A hidden-text filter must not move the reader's indices

- The PDF reader asks PDFium for each character by its index. Hidden characters are turned into
  spaces, not removed, so every later lookup still matches. A first rule (2 points off the page)
  cut a rotated test line in half: the margin became an inch, and the ADR says why.
- **For the template:** filter by replacing, not deleting, when other code addresses by position;
  let the first failing test set the threshold, and write the threshold's reason down.

### XIV.4 "All or nothing" splits into two guarantees

- Keeping the earlier cut until the new one exists is one promise; keeping new parts that succeeded
  is another. Mixing them threw away good work. A result is now defined by its own files, not by
  its folder existing.
- **For the template:** define "a result exists" by content you wrote, never by a container.

### XIV.5 A message shown before a page change is lost

- The windows clear their message line when the step changes, so a message sent before the change
  vanished. The presenter now keeps a notice and shows it after the state is drawn.
- **For the template:** in a presenter, messages tied to navigation are queued until the screen
  they belong to is on.

### XIV.6 A port change breaks every window at once: brief the window agents before it lands

- Adding `show_undo` to the view's port made type-checking fail in three windows until each added
  it. Brief B warned them, so no one "fixed" the lead's code.
- **For the template:** when a shared interface grows, the brief names the new member and says the
  type-check fails until it is implemented.

### XIV.7 Never use `git stash` while other agents edit the same tree

- Comparing old and new outputs with `git stash` would have taken the window agents' unsaved work
  with it if they had written meanwhile. It came back intact, by luck.
- **For the template:** compare against the old code in a separate worktree, never by stashing a
  tree that several agents share.

### XIV.8 Say the claim you can test

- The installer first said the Modern App is "the one a screen reader can read". No one had tested
  it with a screen reader; it now says "works best with one".
- **For the template:** accessibility claims are comparative until a real assistive technology has
  been tried.

### XIV.9 Partial, said as partial

- Not done: each Split part's opening line and headers computed on the whole PDF (B3-03), a Word
  converter of our own (B3-01), a guessed encoding for Markdown read as-is by Merge, white-on-white
  text, the uninstaller's signature, and Review's informative rows in flet (its rows have no tone).
  They are listed in the spec for the fourth audit to check.

## Part XV — What the fourth audit taught (2026-11-09)

The fourth audit used new agents from scratch on 2.12.0, with the third's method: five experts per
board and three conciliators bound by "Claridad es cariño". The owner's decisions were passed to
every auditor as constraints. The score stayed at 7: the release made larger promises, and the
hardest cases still break some of them. Of the third audit's ten recommendations, four were fully
resolved and six partly; none got worse. Of the owner's five decisions, one was fully kept, three
partly, and one waits for SignPath. The conciliators verified 26 groups of findings: 22 confirmed,
4 partly true, none refuted. Report: [`audit/2026-11-09-audit-boards-v4.md`](./audit/2026-11-09-audit-boards-v4.md).

### Product

#### XV.1 A success headline needs a useful result

- A scanned PDF or an empty presentation gave a blank Markdown, and the summary said "converted".
  The empty-input rule (an empty file "failed") was applied to inputs only.
- **For the template:** a result with no text after cleaning is "failed", with its reason, in
  every tool. A rule about inputs is checked against outputs too.

#### XV.2 The hardest case of a text is the shortest one

- One-line fixtures fixed sentences, but two to five bytes ("Sí", "¿Qué?") still decode wrongly.
- **For the template:** for every promise about text, the fixture set starts at two bytes, with
  "¿" and "¡", before it grows to a line.

#### XV.3 One door for every result, and one test that walks every tool

- The output guarantee sat in the worker, so Convert and Split went through it, but Merge's joined
  text did not, and unusual image syntax slipped past the regular expressions.
- **For the template:** the guarantee is applied where the file is written, not where it is made,
  and a test runs every tool with the same hostile fixture.

#### XV.4 One source for a channel, and a test that forbids the others

- The report channel was updated in three messages and missed in a fourth ("Copy Details"), which
  still sent people to a page that needs an account.
- **For the template:** a contact or a promise lives in one catalog key, and a test fails when any
  other text names an older address.

### Applying an audit

#### XV.5 When the code follows an ADR to the letter and still fails, amend the ADR

- The hidden-text filter turns off on a page with any picture, as ADR-0054 says; a letterhead's
  logo is enough to let hidden text through. The fix starts with the decision, not the code.
- **For the template:** check a new ADR's rule against the most common real document (a letter
  with a logo), not only the case it was written for.

#### XV.6 Disagreements settled outside the top ten get a list and a test

- The cheap measures against two runs sweeping each other's temporary files were agreed in the
  third audit but were not in its top ten, and were lost.
- **For the template:** every settled disagreement goes to a pending list with its test, whatever
  its rank.

#### XV.7 An acceptance criterion is checked on every path that reaches it

- "Never lose the list" held for the main path but not for one reached through a check box after
  Split.
- **For the template:** list the paths into each criterion and give each one a test.

### Running an audit

#### XV.8 Constraints from the owner work; conciliators must keep the citations

- Passing the owner's decisions to every auditor removed the recommendations that came back each
  round. The first conciliator lost two ADR citations while regrouping findings.
- **For the template:** a conciliator keeps every ADR citation of the findings it merges, and the
  doctrine conciliator checks the owner's decisions one by one, in the code.

#### XV.9 A verified list that fits in one reading

- About 25 groups can be read at once; a top recommendation that bundles six problems must be
  acceptable in parts.
- **For the template:** cap the verified list at a reading, and make every recommendation
  divisible.

