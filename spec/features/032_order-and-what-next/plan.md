# Plan — Feature 032

- **Presenter** (shared): `InputRow.up` / `InputRow.down` (Merge only); `Presenter.move_input(path,
  offset)`; the dialog after Results answers `keep`, `clear` or `home`
  (`Presenter.what_next(answer)`).
- **Texts**: `gui.main.move_up` / `move_down`; `gui.result.again` = "What Next?" for every tool;
  `gui.more.*` with the third answer `home`; the Welcome's intro and steps.
- **Windows** (ttk, PySide6, flet): ▲ ▼ on each row of Merge's list; the third button of the
  "What Next?" dialog; flet's start screen centred with the shared SVG icons; focus not drawn on
  open.
