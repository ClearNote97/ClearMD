# Plan — Feature 011: Window polish II

> Criteria: [`spec.md`](./spec.md). Decisions: ADR-0027, ADR-0029.

- `components/rail.py`: Settings and Help placed at the band's width and a step's height; the
  `RAIL` button style aligns its text to the left (`brand._button(align="w")`).
- `art.surface(band=, box=, border=)`: the shape ends inside the header band; the page's card
  outline drawn on the ground; `components/surface.py` places the page inside it with a margin.
- `presenter._primary`: with no inputs, the hint of every page is `gui.nav.need_inputs_first`.
