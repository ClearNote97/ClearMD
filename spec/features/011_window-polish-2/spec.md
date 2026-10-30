# Feature 011 — Window polish II

## Goal

What the author asked for after using v0.5.0: Settings and Help as sections of the rail, the
decorative shape never cut by the page, and the line next to the action buttons saying on every
page what is missing (ADR-0027, ADR-0029).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_011_window_polish_2.py`).

- [ ] **AC-01** Settings and Help are as wide and as tall as a step, their mark where a step has
  its number; in the compact rail, their marks alone, centred.
- [ ] **AC-02** The shape at the top right is whole within the header; the page is outlined as a
  soft card, with a margin inside it.
- [ ] **AC-03** With nothing chosen, every page's hint says to add files or folders on Choose;
  with files chosen and no plan, Review and Convert say to press Next on Choose.
- [ ] **AC-04** Everything new follows ADR-0027, in English and Spanish, and has screenshots in
  `docs/screenshots/011/`.
