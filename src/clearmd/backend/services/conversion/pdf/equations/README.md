# pdf/equations — Display equations in a PDF page

Lines and words in, the equations' line ranges out (features 013 and 015). Pure.

| Module | Role |
|---|---|
| `params.py` | The three caps more than one module reads. |
| `model.py` | `Placed`: what the finder needs of a line. |
| `labels.py` | The lines that hold an equation's number at the right margin. |
| `bars.py` | The lines around a fraction's bar (equations with no number). |
| `joins.py` | Whether a line belongs to an equation (no prose, heading or caption). |
| `find.py` | `find_equations`: seeds from numbers and bars, grown up and down. |

`__init__.py` re-exports `Placed` and `find_equations`. Imports `tables.Word` only.
