# odt/mathml — MathML to LaTeX

LibreOffice Math formulas: a subset of presentation MathML → LaTeX (ADR-0024, spec 003). Anything
outside the subset raises `Unsupported` and the whole formula falls back to its StarMath source.
The depth is bounded (`MAX_DEPTH`).

| Module | Role |
|---|---|
| `tables.py` | Greek letters, symbols, functions, accents, fences, variants. |
| `attributes.py` | `Unsupported`, the depth and StarMath constants, what is read off an element. |
| `leaves.py` | `mi`, `mn`, `mo`, and the helpers that join pieces of LaTeX. |
| `rows.py` | Sequences with their fences, and matrices. |
| `scripts.py` | Sub/superscripts and under/over limits. |
| `translate.py` | `translate` (the recursive dispatch), `to_latex`, `starmath`. |

`__init__.py` re-exports `Unsupported`, `to_latex` and `starmath`. `rows` and `scripts` import
`translate` inside their functions (the recursion goes through it); `MAX_FORMULAS` stays in `odt/__init__`.
