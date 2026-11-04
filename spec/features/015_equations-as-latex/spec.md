# Feature 015 — A PDF's equations as LaTeX

## Goal

A PDF's display equations rebuilt as LaTeX from the place of their pieces (ADR-0036), shown as
formulas by viewers with math; equations with no number found too.

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_015_equations_as_latex.py`).

- [x] **AC-01** A fraction drawn with a bar is `\frac{…}{…}`, the equation's number `\tag{N}`,
  as display math (`$$ … $$`) between the text around it.
- [x] **AC-02** An equation with no number is found by its fraction's bar.
- [x] **AC-03** Scripts (`EF_{o}^{t}`), functions (`\max`) and rows (`\begin{array}{l}`).
- [x] **AC-04** With the images folder, an understood equation is LaTeX too (no picture).
- [x] **AC-05** An equation not understood is written as before: its rows as text, or its
  picture with the images folder.
- [x] **AC-06** A ruled table's lines, or a rule in prose, make no equation.
- [x] **AC-07** ADR-0036; version 0.10.0.
