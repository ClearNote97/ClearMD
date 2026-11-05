# odt/writer — ODT elements to Markdown

The writer behind `odt/render.py` (which keeps `OdtRenderer`): one module per kind of element.
The writers are plain functions that take the renderer (`w`), so a level of nesting costs the
same Python frames it always did.

| Module | Role |
|---|---|
| `vocab.py` | Limits, field elements, elements with nothing to show. |
| `state.py` | `OdtState` (one run's budget, counters, footnotes), `FormulaResult`, the `Writer` contract. |
| `formulas.py` | A formula object as Markdown; display math. |
| `paragraphs.py` | Hidden paragraphs, paragraph and heading writers, the sole-formula test. |
| `lists.py` | Numbering, nesting and indentation of `text:list`. |
