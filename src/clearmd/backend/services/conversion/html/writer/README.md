# html/writer — article elements to Markdown

The writer behind `html/render.py` (trafilatura's XML in, ClearMD's Markdown out): standard library
only, with its own architecture rule (`tests/unit/test_architecture.py`). `ArticleRenderer` stays in
`render.py` and the writers are plain functions that take it, so a level of nesting costs the same
Python frames it always did.

| Module | Role |
|---|---|
| `state.py` | Limits, the inline and block tags; later the run's state and the `Writer` contract. |
| `classify.py` | Which children are blocks; where the title is. |
| `shapes.py` | List items, table rows and cells found through wrappers; code text; one-line text. |
| `runs.py` | The properties an inline element sets on its text. |
