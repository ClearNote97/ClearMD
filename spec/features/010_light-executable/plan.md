# Plan — Feature 010: A light executable

> Criteria: [`spec.md`](./spec.md). Decision: ADR-0032.

- `detection/content.py`: `SignatureDetector` in place of magika (the registry builds it).
- `conversion/xlsx.py`: `XlsxConverter` with openpyxl; markitdown without its `[xlsx]` extra.
- `packaging/clearmd.spec`: the heavy libraries excluded, a runtime hook for markitdown's import of
  magika, babel's data trimmed; `notices.py` lists only what ships.
- Tests first; the executables built and checked; reviews; v0.5.0.
