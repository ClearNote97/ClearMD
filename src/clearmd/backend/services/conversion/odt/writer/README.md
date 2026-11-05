# odt/writer — ODT elements to Markdown

The writer behind `odt/render.py` (which keeps `OdtRenderer`: `document`, `blocks`, `inline`, the
recursive entry points): one module per kind of element. The writers are plain functions that take
the renderer (`w: Writer`), so a level of nesting costs the same Python frames it always did.

| Module | Role |
|---|---|
| `vocab.py` | Limits, field elements, elements with nothing to show. |
| `state.py` | `OdtState` (growth budget, counters, footnotes, list numbering), `FormulaResult`, the `Writer` contract. |
| `paragraphs.py` | Hidden paragraphs, properties and roles, paragraph and heading writers, `own_paragraphs`. |
| `formulas.py` | A formula object as Markdown; display math. |
| `frames.py` | Images as placeholders or links, formulas, text boxes. |
| `footnotes.py` | A note's reference and its collected definition. |
| `inline.py` | A paragraph's runs of text (`text_pieces`), code paragraphs as written (`plain_text`). |
| `leaf_blocks.py` | Quotes, code and tables. |
| `lists.py` | Numbering, nesting and indentation of `text:list`. |
| `dispatch.py` | `write_block`: which writer a block-level element goes to. |
| `report.py` | The notes a run earned. |

Imports go one way: `render` → `dispatch` → `lists`/`leaf_blocks` → `inline` → `frames`/`footnotes`
→ `paragraphs` → `formulas` → `state`, `vocab`. Recursion goes through the renderer
(`w.blocks`, `w.inline`), so no module imports the one above it.
