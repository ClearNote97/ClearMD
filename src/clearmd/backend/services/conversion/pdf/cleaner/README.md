# pdf/cleaner — From PDFium's lines to Markdown

`Document` in, `Cleaned` out (feature 008, ADR-0030). What a PDF repeats on every page goes,
broken words and paragraphs are joined, headings are told by their size. Pure: it imports `model`,
never `reader`.

| Module | Role |
|---|---|
| `params.py` | The measures and the sentence end more than one module reads. |
| `sizes.py` | The body's size; each heading size's level; what a heading looks like. |
| `page_numbers.py` | A line that is only a page number (arabic or roman). |
| `running.py` | Running headers, footers and page numbers found and dropped. |
| `joining.py` | A block's lines as one text; broken words joined. |
| `render.py` | Tables, equations and pictures as Markdown blocks. |
| `flow.py` | `Flow`: the block being built; what is measured on it (gap, short, ended). |
| `footnotes.py` | A page's text and its footnotes; `FootnoteQueue` holds them. |
| `buffer.py` | `ParagraphBuffer`: the blocks written; `flush` turns the block being built into one. |
| `headings.py` | Heading level, start, continuation and cut; captions; contents entries. |
| `items.py` | List item markers; the text after one. |
| `writer.py` | `Writer`: each line placed in the flow, in the page's order. |
| `clean.py` | `clean`, `Cleaned`: the entry. |

`__init__.py` re-exports `clean` and `Cleaned`. The writer's state is one `Flow` shared by the
functions of `headings`, `items` and `flow`; none of them owns it, none receives the writer.
Imports: `params` ← `flow` ← `items`; `footnotes` ← `buffer` ← `headings` ← `writer` ← `clean`.
