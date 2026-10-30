# ADR-0034: A PDF's tables, equations and table of contents

- **Status:** accepted
- **Date:** 2026-10-30
- **Refines:** ADR-0030 (the PDF converter: "no tables rebuilt"), ADR-0033 (the images folder).

## Context

The author's examples (a journal paper, a thesis) showed a PDF's tables as runs of loose words,
its numbered equations as scattered pieces ("∑", "J", "j=1" on lines of their own), a table of
contents as one paragraph, and a table's caption joined to the page header or to the paragraph a
page break cut. The author suggested Camelot, crediting it.

Camelot needs OpenCV, Ghostscript and pdfminer: hundreds of megabytes that would undo the light
executable (ADR-0032), and a second PDF reader beside PDFium.

## Decision

- **Camelot's two methods, written anew on PDFium** (credited in the README, "inspired by
  Camelot, MIT"; Camelot is not a dependency).
  - **Lattice** (`pdf/lattice.py`), for ruled tables:
    - the rules are the page's thin paths (≤ 2 points thick, ≥ 10 long), read from PDFium;
    - the rules that cross make a grid, of at least three lines each way (a page frame alone is
      no table);
    - each word goes to the cell it stands in, so a cell wrapped over lines stays one cell.
  - **Stream** (`pdf/tables.py`), for the other words, by where they stand:
    - rows of words whose wide gaps (one font size or more) part cells, four rows or more;
    - the columns come from the rows with the commonest number of cells; a fuller row's cell
      outside them opens one, a header spanning several sets none, a cell bridging two is placed;
    - a table's columns must line up (left, right or centre), its cells hold a number or a word
      (not an aligned formula), and no cell is a line of prose (60 characters at most);
    - a short one-cell row inside it (a group's note, wrapped text) stays in it.
  - **Sideways tables:** a character turned a quarter (either way) is read in its own frame,
    the page turned upright; PDFium runs such rows into one line, so the reader parts them where
    a character goes to another row or changes its turn.
- **Equations** (`pdf/equations.py`):
  - found by their number, "(5)", at the right margin and set apart (alone on its row, or two
    font sizes from what precedes: "… as in (5)" is a reference);
  - their lines are the lines of symbols around it, up to prose (three words of four letters, a
    line ending in ":", or one starting a clause: "where", "donde"), within five line heights;
  - with the images folder: cropped from the page at 144 dpi, trimmed to its ink (a neighbour's
    sliver at the edge goes); else a code block that keeps its rows and columns.
- **Blocks in the page's order:** a table, an equation or a picture closes the paragraph above
  it, as the page sets them (a sentence a table cuts goes on in a new paragraph after it);
  captions ("Table 3:", "Tabla 3.", "Figura 2:") start their own paragraph. A block is never
  taken for a footnote, a running header or a heading (it has no text of its own to weigh).
- **Running headers** on a page set sideways are told by their text alone (their place differs).
- **A table of contents:** a line ending in leaders and a page number ends its entry; a short
  title above the first entry is its own line.

- **Bounded work** (review of 013): every step sorts first and looks up by bisection; a table
  has at most 400 rows and 40 columns, a ruled grid 5,000 cells, a page 50 grids and 200
  equation numbers; a document crops at most 500 equations, within the pictures' pixel budget
  (ADR-0033); a table of contents is read from the line's end, never by a pattern over it.

## Consequences

- Tables, equations and contents read as they were laid out, with no new dependency.
- Heuristics: a table without rules whose columns do not line up stays text; an unnumbered
  equation stays text; a stream table's header spanning columns is placed in its first one.
- Reading a PDF costs about a fifth more (each character's angle and sides are read): 53
  pages/s instead of 66 on the author's 86-page thesis.
- Every cell, every equation row is document text, escaped (ADR-0023); an equation's block is
  fenced longer than any run of backticks in it.
