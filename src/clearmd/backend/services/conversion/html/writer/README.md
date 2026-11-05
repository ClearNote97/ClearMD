# html/writer — article elements to Markdown

The writer behind `html/render.py` (trafilatura's XML in, ClearMD's Markdown out): standard library
only, with its own architecture rule (`tests/unit/test_architecture.py`). `ArticleRenderer` stays in
`render.py` and the writers are plain functions that take it, so a level of nesting costs the same
Python frames it always did.

| Module | Role |
|---|---|
| `state.py` | Limits, the inline and block tags, `ArticleState` (budget, depth, list markers, counters), the `Writer` contract and the notes. |
| `classify.py` | Which children are blocks; where the title is. |
| `shapes.py` | List items, table rows and cells found through wrappers; code text; one-line text. |
| `runs.py` | The properties an inline element sets on its text. |
| `blocks.py` | Headings, quotations and code. |
| `lists.py` | Ordered, unordered and definition lists, their items. |
| `tables.py` | Tables, and `MAX_CELLS` (the module that reads it; tests patch it here). |
| `dispatch.py` | `write_block`: which writer a block element goes to, and the nesting limit. |

Imports go one way: `render` → `dispatch` → `blocks`/`lists`/`tables` → `runs`, `classify`, `shapes`
→ `state`. Recursion goes through the renderer (`w.blocks`); `lists.list_item` imports
`write_block` inside the function, because `dispatch` imports `lists`.
