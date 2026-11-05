# inline — inline text as ClearMD writes it

Pieces of text with their properties in, Markdown out; shared by the `.odt` converter and the HTML
article mode. Standard library and `markdown_out` only.

| Module | Role |
|---|---|
| `pieces.py` | `TextProps`, `Text`, `Raw`, `Piece`, `LINE_BREAK`, `IMAGE_WORD`, `split_space`. |
| `delimiters.py` | The opening and closing delimiter of each style, in nesting order; `without`. |
| `styled.py` | `styled`: runs of text with their delimiters opened and closed. |
| `commonmark.py` | CommonMark's flanking rules and `unpaired_delimiters` (the exact emphasis check). |
| `emphasis.py` | `safe_emphasis`: the styles Markdown would show as literal `*` or `~` are dropped. |
| `normalize.py` | `normalize`: whitespace as HTML and ODF read it; equal neighbours merged. |
| `writer.py` | `InlineWriter`: pieces to Markdown, links by the rules of ADR-0023. |

`__init__.py` re-exports the names other packages use, with `__all__`. Imports: `pieces` ←
`delimiters` ← `styled`, `emphasis` (also `commonmark`) ← `writer` (also `normalize`).
