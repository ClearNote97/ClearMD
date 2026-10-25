# src/clearmd/backend/services/detection — Format detection

- `extension.py` maps the file extension to a format without reading the file; it runs in the CLI process.
- `content.py` asks magika (label table verified on the fixtures); it runs **inside the worker** only.
- `content_policy.py` limits what content may decide: with an unknown extension, only real documents (a docx
  renamed `.dat`), never plain text (`.tex`, `.log`, `.yaml` are not documents to convert).
- `chain.py` tries them in order, cheapest first: content detection runs only when the extension says nothing.
