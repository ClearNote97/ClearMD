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
| `headings.py` | Heading and caption patterns; a table of contents' entry. |
| `items.py` | The markers a list item starts with. |
| `footnotes.py` | A page's text and the small lines at its foot. |
| `writer.py` | `Writer`: the blocks in order. |
| `clean.py` | `clean`, `Cleaned`: the entry. |

`__init__.py` re-exports `clean` and `Cleaned`.
