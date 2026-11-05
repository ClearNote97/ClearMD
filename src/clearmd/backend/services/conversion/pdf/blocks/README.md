# pdf/blocks — Tables and equations in a page

A page's lines in, the same lines with tables and equations as blocks out (features 013 and 015).
Pure: no PDFium, no I/O. `lines.paging` calls `tabled` and `place_equations`; nothing here imports
`lines`.

| Module | Role |
|---|---|
| `tables_on_page.py` | `tabled`: the lines a table covers give way to it (ruled first, then aligned words). |
| `laid_out.py` | An equation's rows, each piece at its place in half-letter columns. |
| `equation_latex.py` | `Found` (what an equation is rebuilt from) and `latex_of`; reads `to_latex`. |
| `equation_blocks.py` | `place_equations`: each equation's lines become one block. |

No `__init__` re-exports. `to_latex` is read in `equation_latex` at call time: a test that
replaces it patches `blocks.equation_latex`.
