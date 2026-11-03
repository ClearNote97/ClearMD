# Feature 014 — Sub- and superscripts, window polish III

## Goal

A PDF's sub- and superscripts as such, its equations whole (ADR-0035); one gutter around and
inside the page; each page's cards shown, faded, before there is anything in them.

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_014_scripts_and_window_polish_3.py`).

- [ ] **AC-01** A numbered equation keeps its tall braces and brackets: it is one block (or one
  picture), never cut there.
- [ ] **AC-02** Sub- and superscripts are written as such: Unicode where it has the letters
  (`EFᵗₒ`, a footnote's `⁵`), `^{…}` / `_{…}` otherwise.
- [ ] **AC-03** One gutter: the window's edge to the rail, the rail to the page's card, the card
  to the window's edges, and the page inside the card, on every side; the smallest window keeps
  the lists' rows (800 × 624).
- [ ] **AC-04** With nothing chosen, Review, Convert and Results show their cards faded ("—"),
  as the rail shows the steps out of reach; with a plan or a result, as before.
- [ ] **AC-05** Screenshots in both themes and languages in `docs/screenshots/014/`.
