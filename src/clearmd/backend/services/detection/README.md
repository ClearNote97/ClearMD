# src/clearmd/backend/services/detection — Format detection

- `extension.py` maps the file extension to a format without reading the file; it runs in the CLI process.
- `content.py` asks magika (label table verified on the fixtures); it runs **inside the worker** only.
- `content_policy.py` runs content detection **only for files without an extension**; an unknown extension
  (`.tex` until feature 002, `.log`, `.dat`) is unsupported without looking inside.
- `chain.py` tries them in order, cheapest first.
