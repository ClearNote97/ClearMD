# Plan — Feature 015: A PDF's equations as LaTeX

> Criteria: [`spec.md`](./spec.md). Decision: ADR-0036.

- `pdf/latex.py` (new, pure): glyphs and bars in, LaTeX or None out; fractions, limits,
  brackets, scripts, rows, words, `\tag`; a balance check.
- `pdf/reader.py`: the page's short level lines (bars) with its rules; each line's characters
  (`span`); an equation's glyphs with PDFium's tight boxes; `Line.latex`; no picture when LaTeX.
- `pdf/equations.py`: equations found by a fraction's bar; prose words in any case.
- `pdf/cleaner.py`: `$$ … $$` as the TeX converter writes it.
- Tests first; the author's examples checked in KaTeX; review; v0.10.0; then stop for the
  author's review.
