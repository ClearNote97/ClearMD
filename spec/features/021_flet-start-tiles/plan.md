# Plan — Feature 021: flet's empty list as two large tiles

> The **how**. Criteria: [`spec.md`](./spec.md). Decision: ADR-0042 (flet), amended.

- `frontend/flet/components/start_panel.py` — `Tile` (a large button: icon, title, text) and
  `StartPanel` (two tiles side by side and a hint, in the list's frame).
- `frontend/flet/components/inputs_card.py` — `show_start(empty)`: the tiles alone, or the small
  buttons, the list and its links.
- `frontend/flet/views/choose.py` — `show_inputs` shows the tiles while no row is listed.
- `frontend/flet/window/controls.py` — the tiles follow `Action.ADD`, as the small buttons.
- `frontend/flet/visuals/look.py` — `tile_style()`.
- `i18n/{en,es}.toml` — `gui.main.start_files`, `start_folder`, `start_hint`; `empty_use_buttons`
  removed.
