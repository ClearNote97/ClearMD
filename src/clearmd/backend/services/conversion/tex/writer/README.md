# tex/writer — LaTeX nodes to Markdown

The writer behind `tex/render.py` (which keeps `render_source`, `render_latex` and the `top_level`
seam): one module per kind of node. `dispatch.Renderer` walks the nodes and calls the others; they
are plain functions that take the renderer (or just its `RenderState`), so a level of TeX nesting
costs the same Python frames it always did (`tests/unit/.../tex/test_recursion_depth.py` pins it).

| Module | Role |
|---|---|
| `vocab.py` | The names the supported subset knows (sectioning, styles, dropped commands, environments). |
| `state.py` | `RenderState` (one run's counters, notes and settings), `ImageHandler`, the `Writer` contract. |
| `structure.py` | Preamble and body, the shallowest sectioning used, babel's main language. |
| `conditionals.py` | Where an `\iffalse` closes; the nodes without what it hides. |
| `expansion.py` | The use of an author's macro, expanded under the budget. |
| `math.py` | Math written back as the author wrote it, with the author's macros expanded. |
| `links.py` | `\href`, `\url` and citations. |
| `lists.py` | `itemize`, `enumerate` and `description`. |
| `floats.py` | Figures and tables: captions, images, `tabular`, includes left in the text. |
| `front_matter.py` | The title block. |
| `environments.py` | `\begin{…}` environments, and the code environments. |
| `commands.py` | `\command` nodes: the ordered chain (its order is behaviour). |
| `dispatch.py` | `Renderer`: `document`, `render`, `inline`, and the node dispatch. |

`__init__.py` re-exports `Renderer`, `ImageHandler`, `is_spanish` and `top_level`, the names
`render.py` uses. Imports go one way: `dispatch` → `commands`/`environments` → the specialists →
`state`, `vocab`.
