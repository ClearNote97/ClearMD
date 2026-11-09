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
