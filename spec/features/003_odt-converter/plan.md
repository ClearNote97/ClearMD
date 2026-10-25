# Plan — Feature 003: `.odt` converter

> The **how**. Criteria: [`spec.md`](./spec.md). Decisions: ADR-0006, ADR-0022, ADR-0023, ADR-0024.

## Architecture

```
src/clearmd/backend/
  schemas/
    formats.py              # + FormatId.ODT, ".odt"; ODT in ZIP_BASED
    notes.py                # + IMAGES_NOT_EXTRACTED, FORMULA_KEPT_AS_SOURCE, REVISIONS_DROPPED,
                            #   TABLE_SIMPLIFIED, ELEMENTS_SIMPLIFIED
    limits.py               # + SECONDS_PER_MIB/MEMORY_PER_MIB[ODT] (benchmark 003); XML limits
  services/
    conversion/
      markdown_out.py       # NEW, shared: escape_text, escape_math, MARK, neutralize, outside_code,
                            #   link_target, safe-link and image-name rules, _join (moved from tex/render.py)
      registry.py           # ODT → OdtConverter
      tex/                  # unchanged behaviour; imports markdown_out
      odt/                  # standard library only
        __init__.py         # OdtConverter: archive → parts → styles → render
        package.py          # mimetype, manifest (encryption), reading a part with a size cap
        xmltree.py          # pyexpat → a minimal element tree, DOCTYPE refused, limits enforced
        styles.py           # automatic + named styles with parents → text and paragraph properties
        render.py           # the subset of the spec, iterative walk
        tables.py           # table:table → Markdown table (merged cells simplified, noted)
        mathml.py           # MathML subset → LaTeX; StarMath fallback
    detection/content.py    # + magika label "odt" → FormatId.ODT
```

`odt/` imports nothing outside the standard library (checked by `tests/unit/test_architecture.py`, which gains
the rule). It is reached only through the registry, inside the worker, like `tex/`.

## Step zero: the shared output module

The guarantee of ADR-0023 is not LaTeX-specific. Before any `.odt` code, the escaping, the block marks, the
final `neutralize` pass, the joining rules and the link and image-name rules move from `tex/render.py` to
`conversion/markdown_out.py`, with their tests. **No behaviour change:** the whole `.tex` suite, the golden
paper and `test_output_guarantee.py` must pass untouched before and after the move.

## Reading (`package.py`, `xmltree.py`)

1. The archive check of feature 001 ran in the plan; the worker reopens the ZIP with `zipfile` (index only).
2. `mimetype` must be `application/vnd.oasis.opendocument.text` (another ODF type → `UNSUPPORTED_FORMAT`).
3. `META-INF/manifest.xml`: an `encryption-data` on `content.xml` → `PASSWORD_PROTECTED`.
4. Each XML part is read with a size cap and parsed by `pyexpat` with namespace processing:
   - `StartDoctypeDeclHandler`, `EntityDeclHandler` and `ExternalEntityRefHandler` raise → `CORRUPT_FILE`;
     `SetParamEntityParsing(NEVER)`.
   - Limits: elements per part, nesting depth, characters per part (`schemas/limits.py`, fixed, ADR-0012).
   - The tree: `Element(tag, attributes, children, text)` with namespace URIs resolved to short prefixes
     (`text:p`); built with an explicit stack, walked with an explicit stack.
5. Formula objects: `draw:object xlink:href="./Object 1"` → the archive entry `Object 1/content.xml`. The name is
   resolved inside the archive only (no `..`, no absolute path, no scheme); at most a fixed number of objects
   per document and a size cap each; past them, the StarMath fallback.

## Styles (`styles.py`)

- Text properties: `fo:font-weight` (bold, or ≥ 600), `fo:font-style` (italic/oblique),
  `style:text-underline-style` (not `none`), `style:text-line-through-style`, `style:text-position`
  (super/sub), `style:font-name` in a set of monospace families, or the named styles `Source_20_Text`,
  `Emphasis`, `Strong_20_Emphasis`.
- Paragraph styles: `Title`, `Subtitle`, `Quotations`, `Preformatted_20_Text`, `Source_20_Code`, found through
  `style:parent-style-name` (automatic styles derive from named ones); a loop in the parent chain stops.
- List styles: `text:list-level-style-number` vs `-bullet` per level; `text:start-value`.

## Rendering (`render.py`)

- The body is `office:body/office:text`. Paragraph-level elements in order; spans resolved to the innermost set
  of properties, emitted as the matching Markdown with escaped text (`markdown_out`).
- Headings: the shallowest `text:outline-level` present maps to `##` (the `Title` paragraph is `#`).
- Notes: `text:note-body` collected, `[^n]` in place, definitions at the end (marked lines).
- Code: consecutive preformatted paragraphs become one fence, text as written.
- Images and formulas: `draw:frame` → placeholder or LaTeX (`mathml.py`); display when the frame is the only
  content of its paragraph.
- Revisions: `text:tracked-changes` regions and `office:annotation` skipped; counted for the note.
- Unknown element: its text kept, its name listed (at most 1,000 distinct, as for `.tex`).

## MathML (`mathml.py`)

A recursive-free translation over the formula's tree: token elements map through tables (Greek letters,
operators, relations, arrows, big operators with limits); `mfrac` → `\frac{}{}`, `msqrt`/`mroot`,
scripts with braces, `munder`/`mover` → limits or accents (`\hat`, `\bar`, `\vec`, `\overline`), fences →
`\left…\right`, `mtable` → `\begin{matrix}…\end{matrix}`, `mtext` → `\text{}`. An element outside the subset
raises inside the translator → the whole formula uses the StarMath `annotation`, or a note when there is none.
The LaTeX goes through `escape_math` like `.tex` math.

## Detection and limits

- `EXTENSIONS[".odt"] = FormatId.ODT`; `content.LABELS["odt"] = FormatId.ODT`; ODT in `ZIP_BASED` (text parts:
  the `.xml` entries, as for docx).
- `SECONDS_PER_MIB[ODT]` / `MEMORY_PER_MIB[ODT]`: provisional until the benchmark (T09).

## Testing strategy

- Unit: each module, with the fixture parts as strings; hostile XML (DOCTYPE, entities, depth, size, element
  count) in `xmltree`; every MathML element in and out of the subset.
- Golden: one reviewed fixture converted exactly (`golden/report.md`), like the `.tex` paper.
- Guarantee: `test_output_guarantee.py` gains an `.odt` corpus (hostile text in spans, links, notes, cells,
  image titles) and the same seeded fuzz.
- Acceptance: `tests/acceptance/test_003_odt_converter.py`, one test per criterion, through the CLI and the real
  worker; the meta-test already covers the new folder.
- **Gate:** pytest, ruff, mypy --strict; review by `code-reviewer` and `security-auditor`, then an adversarial
  verification of the fixes with the CommonMark parser.
