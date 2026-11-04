# ADR-0036: A PDF's equations rebuilt as LaTeX

- **Status:** accepted
- **Date:** 2026-11-04
- **Refines:** ADR-0034 (equations), ADR-0035 (sub- and superscripts).

## Context

v0.9.0 kept a PDF's display equations whole, but as text a fraction is two rows ("0e∕0d" above
"0a∕0b") and a sum's limits stand on rows of their own: the author found it "too inconsistent"
to read. With the images folder an equation was a picture: faithful, but neither text nor
searchable. Equations with no number (three in the author's paper, in a figure) were not found
at all: each piece became a paragraph.

A PDF draws an equation as characters and lines. A fraction's bar is a thin path; PDFium gives
it, and each character's tight box, drawn size and baseline.

## Decision

- **An equation is rebuilt as LaTeX from where its pieces stand**, and written as display math
  (`$$ … $$`, as the TeX converter writes it). VS Code, GitHub and Obsidian show it as a formula;
  it can be copied and searched.
  - **Fractions:** each bar, widest first, with the pieces stacked right above and below it
    (`\frac`); a bar with pieces only below is an overline (`\sqrt` after "√"), only above an
    underline; a short bar alone on a row is a minus.
  - **Sums with limits:** the smaller pieces right above and below "∑" (`\sum_{j=1}^{J}`).
  - **Tall brackets** hold what stands between them (`\left[ … \right]`); a tall brace with no
    closing one holds the rest of its height (`\left\{ … \right.`); an unmatched one is plain.
  - **Scripts:** a smaller piece right after its base, its middle above or below the base's
    axis (`EF_{o}^{t+1}`), runs of them together.
  - **Rows** by their axis (`\begin{array}{l} … \\ … \end{array}`); words inside ("if", "can"),
    functions (`\max`) and operators with limits (`\operatorname*{Max}_{z}`) as such; its number
    at the right as `\tag{7}`.
  - The tight character box is asked of PDFium only for an equation's characters.
- **Only what is understood is written.** A piece that cannot be read, more than 600 characters
  or 12 rows, a formula a check of braces, `\left`/`\right` and environments would refuse: the
  equation is written as before (its picture with the images folder, else its rows as text).
- **With the images folder, LaTeX too** when it is understood: one way to read an equation,
  copyable; the picture stays the way when it is not.
- **Equations with no number** are found by a fraction's bar: a short line drawn (at most 60 % of
  the text's width) with words right above and below it, on lines that are no prose and that hold
  a relation ("=", "≤", "∈"…). A bar repeated just above or below with the same ends is a ruled
  table's, never a fraction's. A line with three words of four letters or more is prose, whatever
  their case ("The Malmquist Output-Based Productivity Index…").

## Review

An adversarial review found 15 points; 14 were fixed, each with a test:

- **Never a failure:** an equation of many sizes, none shared, made the whole file fail; now
  any error inside the rebuild means "unsure".
- **Never a wrong formula, said with confidence:**
  - A numerator stops at the row beside it.
  - A glyph PDFium cannot read (a code with no map, half a character, a font without a map, a
    character drawn nowhere) makes the equation unsure, never dropped.
  - Accents go on their letter (`\hat{x}`), and a lone one is unsure.
  - Controls, marks and direction changes are unsure.
  - Degrees and primes are written so a script can follow them (`x^{2}{}^{\circ}`).
  - Limits under a word are merged.
  - An "=" drawn as two lines is "="; tall bars pair as `\left| … \right|`.
  - Words need four letters ("abc" stays a product).
  - At most 64 drawn lines per equation.
- **Detection:**
  - A footnotes' rule (at the column's start, smaller text under it) or a rule under a line (a
    word across its end) is no fraction's bar.
  - Capitalised words make prose only around an equation with no number, so a numbered one keeps
    a row of named variables.
- **Left as it is:** two fractions of the same width stacked closer than 40 points read as a ruled
  table when they have no number (the output is the text, never a wrong formula).

## Consequences

- On the author's paper all 15 equations are LaTeX (13 numbered, 2 in a figure) and each renders
  in KaTeX (checked); on the thesis nothing changes (its ruled tables stay tables).
- An equation is as faithful as its drawing: "s.a." drawn as "s ⋅ a" stays so; the author's "x"
  for a product is a letter; the alignment of a system's rows is not kept (each row from the left).
- A viewer without math shows the LaTeX source: still readable, and exact.
- Supersedes ADR-0034's "a picture with the images folder" for the equations that are understood.
