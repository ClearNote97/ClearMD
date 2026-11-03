# ADR-0035: A PDF's sub- and superscripts

- **Status:** accepted
- **Date:** 2026-11-03
- **Refines:** ADR-0030 (the PDF converter), ADR-0034 (equations).

## Context

A PDF has no sub- or superscripts: they are smaller characters drawn higher or lower. PDFium
gives them as plain letters, often on lines of their own, so `EFᵗₒ` read "EFt o", `Rᴺ₊` read
"RN +", and a footnote's mark was a plain digit glued to the word. The author found equations
and inline mathematics hard to read.

## Decision

- **A script** is a character drawn smaller than its line's text (85 % or less), its baseline
  raised (12 % of the size) or lowered (8 %) from the letter it is set on.
  - The size is the one drawn: the font's size scaled by the height of the text's matrix (PDFs
    set "1 Tf" and scale by the matrix; a horizontal scale alone changes no size).
  - The text's size is the largest one many characters share, never a tall delimiter's.
  - The baseline is compared with the nearest letter or digit of the text's size (a PDFium
    "line" may hold two rows of a paragraph; a "∑" has its own baseline).
- **Written as Unicode** where every character of the script has a form (`ᵗ`, `ₒ`, `ᴺ`, `₊`,
  `ⱼ`, `²`), readable in any viewer and by any tool; else as `^{…}` or `_{…}` (TeX's notation,
  plain text).
- **A line PDFium ends where its row goes on** (the next character on the same row, right after
  the last) is one line; a space between its pieces, gone when it touches a script.
- **Equations:** a tall brace, bracket or sum is part of its equation (only words larger than
  the equation's number make a heading); an equation is measured by its number's size; its
  picture stops at the lines just above and below it.

## Consequences

- Inline mathematics and footnote marks read as written; display equations stay whole.
- A fraction or a sum with limits above and below, as text, stays hard to read: with the images
  folder it is a picture.
- Reading a PDF asks PDFium two more things (the matrix and the origin), only when a font or a
  size changes along the page: about a tenth slower, 70 pages/s on the author's thesis (78 in
  v0.8.0). Each step is linear: a hostile page of 200,000 characters reads in under a second.
- A lone operator set smaller between two terms ("1 ∗ 0.169") is no script; a footnote that
  starts with a raised mark ("¹First note") is still a note of its own.
- In the raw Markdown a subscript with no Unicode letter reads `\_{q}` (the underscore escaped,
  as every document underscore is); a viewer shows `_{q}`.
