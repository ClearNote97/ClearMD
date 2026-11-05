# src/clearmd/backend/services/detection — Format detection

- `extension.py` maps the file extension to a format without reading the file; it runs in the CLI process.
- `content.py` asks ClearMD's own signatures (`detect_format`, `SignatureDetector`); it runs **inside the worker** only.
  `text_signatures.py` tells HTML, notebook, TeX, code and CSV in a text sample; `zip_signatures.py` tells a ZIP's format
  (DOCX, PPTX, XLSX, ODT, EPUB) by its parts.
- `content_policy.py` runs content detection **only for files without an extension**; an unknown extension
  (`.tex` until feature 002, `.log`, `.dat`) is unsupported without looking inside.
- `chain.py` tries them in order, cheapest first.
