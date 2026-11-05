# markdown_out — Markdown that never does what the document did not write

The output guarantee shared by ClearMD's own converters (ADR-0023, ADR-0024). Standard library only.

| Module | Role |
|---|---|
| `marks.py` | `MARK`, the fence patterns, and the line helpers (`block`, `indent`, `marked`, `line_endings`…). |
| `code.py` | `fence_for`, `inline_code`, and `outside_code`, the scanner that leaves fenced code alone. |
| `escaping.py` | `escape_text`, `escape_math`, `join_pieces`, `link_target`, `heading_text`, `ENTITY`, `SAFE_LINK`. |
| `neutralize.py` | `neutralize`, `math_line` and `tidy`: the final passes over a whole text. |

`__init__.py` re-exports the public names with `__all__`. Imports: `marks` ← `code` ← `neutralize`;
`escaping` ← `marks`.
