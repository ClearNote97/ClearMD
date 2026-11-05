# conversion/html — Web pages (feature 004)

The whole page goes through markitdown; the article mode (ADR-0025) lets trafilatura find the
article and ClearMD write it. Laid out by refactor R01 (ADR-0039).

| Module / package | What |
|---|---|
| `__init__.py` | The converter: whole page or article, and the fallback to the whole page |
| `page.py` | The page's bytes and encoding, read without fetching anything (ADR-0005) |
| `render.py` | `ArticleRenderer`: the article's tree into Markdown (its recursive entry points) |
| `writer/` | What the renderer writes, one concern per module (state, classify, shapes, runs, blocks, lists, tables); the standard library only |
