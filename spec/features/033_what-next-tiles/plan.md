# Plan — Feature 033

- **Presenter:** `NextChoice(tool, title, current)`; `Presenter.next_choices()` (the tool just used
  first); `Presenter.continue_with(tool, keep=…)` replaces 032's `what_next(answer)`.
- **Texts:** `gui.more.{title, convert, split, merge, again, keep, keep_help, cancel}`.
- **Windows:** each one's "What Next?" dialog redrawn: three small tiles (the shared tool icons of
  `design/tool_art.py`), the box, Cancel.
