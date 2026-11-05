# frontend/design — Design tokens

What every GUI (ttk, PySide6, later flet) draws with, as plain data (ADR-0027, ADR-0039):

| Module | What |
|---|---|
| `palette.py` | The light and dark palettes |
| `metrics.py` | The 8 px grid, the window's sizes, radii, the rail's widths |
| `typography.py` | Text sizes in pixels (each toolkit converts them to its own units) |
| `colors.py` | `blend`: one colour laid over another |
