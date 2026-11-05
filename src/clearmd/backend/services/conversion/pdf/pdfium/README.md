# pdf/pdfium — Everything that calls PDFium

The reader's only contact with PDFium's C API (pypdfium2's raw bindings, feature 008, ADR-0030). The
steps after it (`lines`, `blocks`, `cleaner`) work on plain data and never touch PDFium.

| Module | Role |
|---|---|
| `document.py` | `opened`: the document and its load errors; the pages; `finite`. |
| `fonts.py` | `Fonts`: a number per font, its codes, errors and weight; the first pass. |
| `page_chars.py` | One page's characters, compact (the hot loop); tight character boxes. |
| `page_objects.py` | A page's thin paths: ruled-table rules and fraction bars. |
| `image_objects.py` | A page's image objects with their place, forms' included. |
| `pictures.py` | The pictures as lines, within the document's pixel budget. |
| `crop.py` | An equation as it looks on the page, rendered and trimmed. |

No `__init__` re-exports: importers name the module (`pdfium.document.opened`). Imports:
`document` ← `fonts`, `page_chars`, `page_objects`, `image_objects` ← `pictures` ← `crop`.
The pixel and crop budget (`list[int]`) is built by `reader.read` from its own
`MAX_DOCUMENT_PIXELS` and `MAX_CROPS`.
