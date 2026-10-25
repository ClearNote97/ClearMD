# src/clearmd/backend/services/conversion/odt — The OpenDocument text converter (feature 003)

ClearMD's own converter for `.odt`, with the standard library only (ADR-0006): `zipfile` for the package and
`pyexpat` for its XML, behind ClearMD's own limits (ADR-0024). Imported only inside the worker process. Its
Markdown goes through `../markdown_out.py`, the output guarantee shared with the `.tex` converter (ADR-0023).
The rules are in ADR-0024 and `spec/features/003_odt-converter/`.
