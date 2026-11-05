# pdf/tables — Tables in a PDF page

Words in, tables out (feature 013, ADR-0034). Pure: no PDFium, no I/O.

| Module | Role |
|---|---|
| `params.py` | The four limits more than one module reads. |
| `rows.py` | `Word`, `Table`, the rows of a page and their cells. |
| `columns.py` | The columns, as Camelot's stream method finds them. |
| `grid.py` | Where cells fall in the columns; whether the columns are aligned. |
| `build.py` | A run of rows made a table, or refused (formula, list, prose). |
| `find.py` | `find_tables`: the runs of tabular rows of a page. |

`__init__.py` re-exports `Word`, `Table` and `find_tables`. Imports: `rows` ← `columns`, `grid` ← `build` ← `find`.
