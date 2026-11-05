# tests/fixtures/tex — LaTeX fixtures (feature 002)

Written by `../builders/tex.py` (`build_tex`, run by `../build_fixtures.py`); do not edit by hand.

- `paper.tex` — every row of the supported subset; `img/plot.png` for its figure.
- `thesis/` — a main file with `\input`/`\include`, chapters, an include two levels down, the author's macros in
  `macros.tex`, `\graphicspath` and an image.
- `latin1.tex` / `latin1_undeclared.tex` — the same text in latin1, with and without `inputenc`.
- `unknown.tex`, `multicolumn.tex`, `malformed.tex` — what must produce notes, never a crash.
- `no_extension_latex` — detection by content.
- `hostile/` — includes that must not be followed (absolute, `..`, non-`.tex`, missing, cycle, 10 levels deep) and
  macro bombs (recursive, and 40 doublings). A link and 201 includes are created by the tests themselves.
