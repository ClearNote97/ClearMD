# pdf/lines — From a page's characters to its lines

`Chars` in, `Page` out (features 008, 013, 014). Pure: no PDFium, no I/O. `paging` is the entry; it
hands the finished lines to `blocks` for tables and equations.

| Module | Role |
|---|---|
| `paging.py` | `build_page`: the characters split into lines, then tables and equations found. |
| `breaks.py` | Where a line PDFium ends goes on; where a sideways row starts another. |
| `assemble.py` | `build_line`: one line's text, size, weight and place; the words it holds. |
| `words.py` | `build_word`: a word's box in its frame; `width`. |
| `scripts.py` | A line's text with its scripts written as such. |
| `script_marks.py` | Which characters are scripts, raised or lowered. |

No `__init__` re-exports. Imports: `words` ← `breaks`; `script_marks` ← `scripts` ← `assemble`;
`assemble`, `breaks` and `blocks` ← `paging`.
