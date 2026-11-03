# Plan — Feature 014: Sub- and superscripts, window polish III

> Criteria: [`spec.md`](./spec.md). Decision: ADR-0035.

- `pdf/reader.py`: each character's drawn size and baseline; lines PDFium ends mid-row joined;
  scripts marked and written (Unicode or `^{…}` / `_{…}`).
- `pdf/equations.py`: a tall delimiter is no heading; the number's own size.
- `layout.GUTTER` for every edge; `MIN_HEIGHT` 624.
- `brand.DIM_CARD` / `DIM`; Review, Convert and Results wait faded.
- Tests first; screenshots; review; v0.9.0; then stop for the author's review.
