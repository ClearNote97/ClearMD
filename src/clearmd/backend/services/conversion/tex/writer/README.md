# tex/writer — LaTeX nodes to Markdown

The writer behind `tex/render.py`: one module per kind of node. Moves in progress; the table is
completed with the class decomposition.

| Module | Role |
|---|---|
| `vocab.py` | The names the supported subset knows (sectioning, styles, dropped commands, environments). |
| `structure.py` | Preamble and body, the shallowest sectioning used, babel's main language. |
| `conditionals.py` | Where an `\iffalse` closes among sibling nodes. |
| `floats.py` | Which environments are floats and which caption is theirs. |
| `math.py` | Math written back as the author wrote it. |
| `state.py` | The callback types the writer is given. |
