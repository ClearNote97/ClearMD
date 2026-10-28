# Plan — Feature 005: Presenter (MVP) + ttkbootstrap GUI

> The **how**. Criteria: [`spec.md`](./spec.md). Decisions: ADR-0001, ADR-0008, ADR-0012, ADR-0013, ADR-0016,
> ADR-0026, ADR-0027 (visual identity). Contract: [`spec/contracts/ux.md`](../../contracts/ux.md).

## Architecture

```
src/clearmd/
  backend/
    schemas/settings.py        # + last_output_folder
    services/settings_store.py # + save_settings (atomic, known keys only)
    services/folders.py        # open_folder (moved from the CLI: shared by every interface)
    api/__init__.py            # + save_settings, open_folder
  frontend/
    presenter/                 # standard library only (architecture rule)
      state.py                 # AppState (the seven states) and what each enables
      models.py                # what the view draws: InputRow, PlanView, ProgressView, ResultView…
      ports.py                 # View protocol; Backend protocol (the api functions it uses)
      presenter.py             # the intents (add, remove, analyze, confirm, cancel, open, settings…)
      texts.py                 # every text the view shows, from the catalogs
      system_theme.py          # light or dark, from the operating system (no dependency)
    assets/                    # ADR-0027: logo (SVG, PNG, app icon) and file icons (PNG), for every GUI
    presenter/icons.py         # which icon a path gets (by format; folder, Markdown, unknown)
    ttk/                       # ttkbootstrap + tkinterdnd2
      app.py                   # the root window, the theme, the scheduler (after), main()
      layout.py                # the 8 px grid, the fonts (14 px body)
      brand.py                 # the palette, the clearmd-light/-dark themes, rounded image elements
      art.py                   # Pillow drawings: rounded shapes, the background shape, row images
      views/                   # main, plan, progress, result, help, welcome, settings
      components/              # the rail, cards, the drop zone, the file list
tests/
  unit/frontend/presenter/     # every intent and state, with a fake view and a fake backend
  unit/frontend/ttk/           # widgets under xvfb (skipped without a display)
  gui/screenshots.py           # every screen, light/dark, EN/ES → docs/screenshots/005/
  gui/make_assets.py           # draws the logo and the file icons (one geometry → SVG and PNG)
  acceptance/test_005_ttk_gui.py
```

## Steps

1. **Settings written, folders opened.** `save_settings` (atomic write through a temporary file, unknown keys
   dropped, the same validation as reading), `last_output_folder`, `open_folder` moved out of the CLI.
2. **The presenter, test first.** The states and their enabled actions; the intents; the worker thread and
   the scheduler; every text from the catalogs; a fake view and a fake backend that records calls.
3. **The ttk shell.** Root window with tkinterdnd2 and ttkbootstrap, theme from the setting or the system,
   the layout constants, the main view with Add files / Add folder / drop zone / input list / output choice /
   Convert / "?" / settings.
3b. **The visual identity (ADR-0027).** The asset script and its drift test; the two themes; rounded
   buttons and cards; the rail with the logo and the steps; the main view rebuilt on it, with the numbered
   file list and its icons.
4. **Plan, progress, result.** The plan review (counts, skipped with reason and action, existing outputs and
   the choice), the progress (i of n, file, bar, time left, long-file timer, Cancel), the result (counts,
   problems in plain words, Open results folder, the folder opened by itself).
5. **Help, welcome, settings.** The three dialogs; Esc closes them; Restore defaults.
6. **Keyboard and look.** Tab order, Enter, Esc, the 8 px grid and 14 px checks, both themes.
7. **Screenshots, acceptance, close.** The screenshot script under xvfb; the acceptance tests; READMEs, roadmap,
   reviews (code review, security audit with runnable proofs, an adversarial verification of the fixes).

## The presenter contract (what every GUI implements)

- `View.show_state(state, enabled)`, `show_inputs(rows)`, `show_output_choice(choice)`, `show_plan(plan)`,
  `show_progress(progress)`, `show_result(result)`, `show_message(text)`, `ask_existing(existing) → decision`,
  `schedule(callback)`.
- Intents: `add_paths`, `remove_input`, `clear_inputs`, `choose_output_next_to`, `choose_output_folder`,
  `analyze`, `confirm`, `back`, `cancel`, `open_results`, `dismiss_welcome`, `save_settings`,
  `restore_defaults`.

## Testing strategy

- **Presenter (no display):** every state transition and enabled action; inputs de-duplicated; the output
  choice remembered; the plan view's wording; progress texts; cancel; failures; settings save/restore; the
  welcome once; the worker thread with a synchronous scheduler and with a real thread.
- **ttk (xvfb):** each view builds; the primary action and Enter; Esc; tab order; theme switch; layout
  constants; a real batch on fixture documents through the GUI with the real worker.
- **Acceptance:** one test per criterion.
- **Screenshots:** generated, not hand-made; the script checks each screen renders without errors.
