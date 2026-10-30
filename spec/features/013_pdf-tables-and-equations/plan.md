# Plan — Feature 013: PDF tables and equations

> Criteria: [`spec.md`](./spec.md). Decision: ADR-0034.

- `pdf/tables.py` (stream) and `pdf/lattice.py` (lattice): pure, words and rules in.
- `pdf/reader.py`: character boxes and turns, words per frame, rows split in sideways text, the
  page's rules, tables replace the lines they cover; equations gathered, cropped with images.
- `pdf/equations.py`: pure, lines and words in.
- `pdf/cleaner.py`: table, equation and caption blocks; contents entries; turned headers.
- Tests first on hand-made PDFs; the author's examples evaluated locally; review; v0.8.0.
