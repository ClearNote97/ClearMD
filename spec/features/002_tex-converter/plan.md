# Plan — Feature 002: `.tex` converter

> The **how**. Criteria: [`spec.md`](./spec.md). Decisions: ADR-0006, ADR-0022.

## Architecture

```
src/clearmd/backend/
  schemas/
    formats.py              # + FormatId.TEX, ".tex"
    notes.py                # NoteKind, ConversionNote (language-neutral facts)
    models.py               # ConversionOutcome.notes
  services/
    conversion/
      registry.py           # DocumentConverter now returns ConversionResult(markdown, notes)
      markitdown_adapter.py # returns ConversionResult(markdown, ())
      tex/                  # imported only inside the worker (pylatexenc)
        __init__.py         # TexConverter: read → resolve → expand → render
        source.py           # reading: encoding (UTF-8 → inputenc → detected), size accounting
        includes.py         # safe resolution of \input/\include/\subfile inside the document folder
        macros.py           # the author's macro table and the expansion budget
        render.py           # node visitor → Markdown (the subset of the spec)
        tables.py           # tabular → Markdown table, or a LaTeX block when it cannot be faithful
    detection/content.py    # + magika label "latex" → FormatId.TEX
    worker/protocol.py      # Converted.notes
    summary/writer.py       # "Converted with notes" section
  frontend/cli/app.py       # one line per file with notes
```

`services/conversion/tex/` depends on `pylatexenc` and on the standard library; it is reached only through the
registry inside the worker (the architecture test and AC-03 enforce it).

## Contracts

```python
# schemas/notes.py
class NoteKind(StrEnum):  # unknown_commands, include_not_followed, macro_limit_reached,
    ...  # table_kept_as_latex, encoding_guessed, parse_recovered


class NoteReason(StrEnum):  # outside_folder, absolute, parent_segment, link, not_tex, missing,
    ...  # cycle, too_deep, too_many, too_large, expansions, nesting, growth


@dataclass(frozen=True)
class NoteItem:
    subject: str  # a command, a path, an encoding...
    reason: str = ""  # a NoteReason value, translated by the catalog


@dataclass(frozen=True)
class ConversionNote:
    kind: NoteKind
    items: tuple[NoteItem, ...] = ()


# schemas/models.py (crosses the worker boundary and the runner port)
@dataclass(frozen=True)
class ConversionResult:
    markdown: str
    notes: tuple[ConversionNote, ...] = ()


# services/conversion/registry.py
class DocumentConverter(Protocol):
    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult: ...
```

- `ConversionRunner.convert` returns the same `ConversionResult`; `execute_plan` keeps the notes in
  `ConversionOutcome.notes` (status stays `CONVERTED`).
- Notes are facts, never sentences: the catalog turns them into words (`note.unknown_commands`: "commands ClearMD
  does not know were left as written: {items}").
- Reasons are `NoteReason` codes, translated by the catalog (`note.reason.<code>`); the summary lists at most 20
  items per note, then "and N more".

## The pipeline inside `TexConverter` (as built, after the review: ADR-0023)

1. **Read** (`source.py`): bytes → text. UTF-8 first; if it fails, the encoding named in
   `\usepackage[…]{inputenc}` (latin1 is read as cp1252, latin9/cp1252 map to Python codecs); else
   `charset_normalizer` (already installed with markitdown) and an `encoding_guessed` note.
2. **Splice includes** (`document.py`): in TeX an `\input` inserts text, so each allowed include (outside
   comments and code) is read once, on one budget, decoded and spliced in place, recursively; a refused one stays
   in the text. A map of the pieces turns a parse position back into `file, line N`.
3. **Parse once** (`context.py`): a tolerant walker with ClearMD's specs keeps the first error it recovered from.
   **Collect macros** (`macros.py`) in document order; parse again with the author's argument specs only when a
   definition has arguments or a name pylatexenc already knows.
4. **Render** (`render.py`): a visitor over the nodes, writing Markdown. Text-mode nodes follow the subset table;
   a user macro is expanded (budget charged) and its result parsed and rendered in place; math nodes are
   re-serialized from their nodes with user macros expanded, comments dropped and nothing else touched (AC-10).
   Unknown macros and environments are written back verbatim (`node.latex_verbatim()`) and recorded for the
   note. If pylatexenc cannot read the source at all, it is kept whole as a LaTeX block with a note.
5. **Assemble**: title block, body, footnotes at the end; collapse runs of blank lines outside code blocks.

## Includes (`includes.py`)

```python
def resolve_include(argument: str, state: IncludeState) -> Path | NoteReason
def enter(argument: str, state: IncludeState) -> tuple[Path, bytes] | NoteReason  # cycles, limits, read
```

- Paths resolve against the main file's folder, as in LaTeX.
- Rejected before touching the disk: absolute paths, drive letters, any `:` (a scheme), `~`, `..` segments,
  NUL, empty names.
- `.tex` appended when there is no suffix; only `.tex` accepted.
- Every component from the document folder down is checked with `lstat` (no links, no junctions), the target must
  be a regular file, and its resolved path must stay inside the resolved document folder.
- `IncludeState` tracks the stack (cycles), depth (≤ 8), the count (≤ 200) and the bytes read (≤ 250 MiB, the
  main file included). The read walks the folders by descriptor with `O_NOFOLLOW` (`read_inside`).
- The relative directory for `\includegraphics` stays the one of the **document folder** (LaTeX resolves
  graphics from the main file's folder), with `\graphicspath{{img/}}` honored when present.

## Macros (`macros.py`)

- `MacroDefinition(name, n_args, default_first, body)`; `\renewcommand` replaces; `\providecommand` keeps the first.
- Expansion substitutes `#1…#9` in the body in one pass (`##` is `#`) and re-parses the result.
- `MacroExpander` counts expansions (≤ 10,000), the current nesting depth (≤ 64) and the size produced
  (≤ 4 × source + 1 MiB, charged before the text is built). When exceeded, it raises `BudgetExceeded`; the
  renderer writes that top-level use as written, stops expanding for the rest of the document, and records a
  `macro_limit_reached` note naming the macro and the limit.

## Rendering rules worth fixing now

- Heading levels: the shallowest sectioning command present maps to `##` (the title is `#`); deeper levels follow,
  capped at `######`.
- Lists: continuation lines are indented by the width of their marker (CommonMark); `enumerate` restarts per
  list; `description` items become `- **term** text`; text before the first `\item` stays before the list.
- Code: `lstlisting [language=Python]` and `minted{python}` give the fence language.
- Tables: a cell may contain inline formatting and math; `|` inside a cell is escaped; rows end at `\\`; the first
  row is the header; `\multicolumn`/`\multirow` → the whole `tabular` verbatim in a ```` ```latex ```` block and a
  `table_kept_as_latex` note.
- Images: the target is `os.path.relpath(image, start=output_md.parent)` with `/` separators; the converter
  receives the output path through the request (a new `ConvertRequest.target` field). Only image files are
  looked up; a name outside the folder or remote is shown as code, never as a link (ADR-0023).
- Floats: everything inside is rendered in order; the caption becomes the alt text of a single image, otherwise
  an italic line under the float (each `subfigure` has its own).
- Abstract heading: babel's main language (its last option, else the class's language option, or polyglossia's
  `\setmainlanguage`) Spanish → "Resumen"; anything else → "Abstract". This is the document's language, not the
  app's.

## Detection and limits

- `EXTENSIONS[".tex"] = FormatId.TEX`; `content.LABELS["latex"] = FormatId.TEX`.
- `SECONDS_PER_MIB[TEX]` and `MEMORY_PER_MIB[TEX]`: provisional values (`0.5` s, `8` MiB/MiB) until the
  benchmark case (T10) replaces them.
- The archive check does not apply (not a ZIP); the worker's time and memory limits do.

## Summary and CLI

- Summary: a section **"Converted with notes"** after "Converted": one item per file, one sub-line per note
  (`- `chapter.tex` — commands ClearMD does not know were left as written: `\foo`, `\bar``). Converted files with
  notes stay in the name table too.
- CLI: after the file's progress line, `ℹ name — converted with notes (see the summary)` unless `--quiet`.
- Totals unchanged ("converted"); notes never change the exit code.

## Testing strategy

- **Fixtures** (`tests/fixtures/tex/`, written by `build_fixtures.py`): `paper.tex` (the whole subset), a thesis
  folder (`thesis/main.tex` + `chapters/*.tex` + `macros.tex` + `img/plot.png`), `latin1.tex` (with and without
  `inputenc`), `unknown.tex`, `hostile/` (absolute include, `..` include, include through a link, cycle, depth 9,
  201 includes, recursive macro, exponential macro, unclosed group, stray `\end`), `no_extension_latex`.
- **Unit:** `includes` (every refusal reason, the document-folder boundary), `macros` (arguments, optional
  default, renew/provide, budget limits), `render` (one test per row of the subset table, table golden files),
  `source` (encodings), notes in the summary writer (EN/ES).
- **Acceptance:** `tests/acceptance/test_002_tex_converter.py`, one test per AC, through `cli.main`; the meta-test
  of feature 001 is extended to every feature folder.
- **Benchmark:** a generated `.tex` case (text + math + includes) added to `run_benchmark.py`.
- **Gate:** pytest, ruff, mypy --strict; review by `code-reviewer` and `security-auditor` (includes and macros
  are attack surface), with an adversarial verification of their fixes.
