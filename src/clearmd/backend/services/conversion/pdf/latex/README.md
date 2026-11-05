# pdf/latex — A display equation rebuilt as LaTeX

Characters and bars in, a LaTeX string (or None) out (feature 015, ADR-0036). Pure.

| Module | Role |
|---|---|
| `params.py` | The two measures more than one stage reads. |
| `unsure.py` | The exception every stage raises when a piece has no rule. |
| `symbols.py` | The tables: brackets, big operators, Greek and math symbols, accents. |
| `nodes.py` | `Glyph`, `Bar` and the `Node` built from a glyph. |
| `envelope.py` | The equation's number as `\tag`; the balance check. |
| `accents.py` | An accent put on the piece below it. |
| `stacking.py` | What stands above or below a bar; the sizes around it. |
| `fractions.py` | A bar with its numerator and denominator: fraction, root, overline. |
| `operators.py` | A sum's limits. |
| `brackets.py` | Tall brackets with what they hold. |
| `scripts.py` | Where a small piece is set on a base; how scripts are written. |
| `row_text.py` | A row's pieces joined: words, spaces, quads. |
| `rows.py` | The pieces in rows by their axis, each small piece on its base. |
| `layout.py` | The dispatcher, in order: fractions, accents, limits, brackets, rows. |
| `writer.py` | `to_latex`: the entry. |

`__init__.py` re-exports `to_latex`, `Glyph`, `Bar`, `MAX_ROWS` and `MAX_GLYPHS`.

Fractions, limits, brackets and rows call `layout` back for what they hold. Each imports it inside
the function that calls it, so there is no module cycle and no extra stack frame on the
recursion (`MAX_DEPTH` and `RecursionError` behave as before).
