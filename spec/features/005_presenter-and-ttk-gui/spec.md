# Feature 005 — Presenter (MVP) + ttkbootstrap GUI

## Goal

A person who has never opened a terminal converts a folder of documents to Markdown in a window: chooses
files or a folder (or drops them), sees what will happen, confirms, watches the progress, and opens the
results — without the window ever freezing, surprising them, or speaking in technical terms.

## Scope

- **Includes:**
  - The presenter (ADR-0026): the states, the texts and the interaction logic, shared by every GUI.
  - The ttkbootstrap GUI on top of it, following `spec/contracts/ux.md`: main window, plan review, progress,
    result, help, welcome, settings; light and dark themes; drag and drop; keyboard.
  - Writing `settings.toml` (atomic, known keys only) and the new `last_output_folder` setting.
  - A GUI entry point, `clearmd-ttk`.
  - Screenshots of every screen (light and dark, English and Spanish) in `docs/screenshots/005/`.
  - The visual identity (ADR-0027): themes, rail, logo, file icons.
- **Does not include:** executables, code signing and the startup splash (feature 006); PySide6 and flet
  (007–008); new conversion features.

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test named after its id (`tests/acceptance/test_005_ttk_gui.py`). Tests that
need a window run under a virtual display.

### The presenter

- [x] **AC-01** The presenter is in exactly one of the seven states of the contract at any time, and each state
  says which actions are enabled (Convert only with inputs; Cancel only while analyzing or converting).
- [x] **AC-02** Planning and converting never run on the UI thread: the UI thread stays responsive (it handles
  events) while a batch runs, and every presenter update happens on the UI thread.
- [x] **AC-03** Every text the presenter gives the view comes from the catalogs, in the chosen language
  (EN/ES); rejections use the shared wording (kind, precise reason, what to do).
- [x] **AC-04** The presenter imports only `backend.api`, `backend.schemas`, `i18n` and the standard library.

### Choosing what to convert

- [x] **AC-05** **Add files** and **Add folder** open the native dialogs; dropping files or folders on the window
  adds them; an input can be removed; the same input is never listed twice.
- [x] **AC-06** The output choice is "next to the originals" (default) or a folder the user picks; the picked
  folder is remembered as the suggestion for next time (`last_output_folder`).

### Before converting

- [x] **AC-07** **Convert** first shows the plan: how many files will be converted, which are skipped and why
  (with what to do), and which outputs already exist; nothing is written until the user confirms.
- [x] **AC-08** With outputs that already exist and the setting `ask`, the plan asks what to do with them
  (overwrite or keep); `overwrite` and `skip` settings are honoured without asking.

### Converting

- [x] **AC-09** While converting: "*i* of *n*", the current file, a progress bar, the time left in plain words,
  and, for a file that takes long, a running timer and "large files can take a few minutes".
- [x] **AC-10** **Cancel** is always available while a batch runs, stops the current file at once, and the state
  becomes Cancelled; the summary of what was done is still written.

### After converting

- [x] **AC-11** The result shows converted / skipped / failed (and stopped), each failure in plain words with
  what to do, and **Open results folder**; by default the folder opens by itself (setting
  `open_output_when_done`).
- [x] **AC-12** One failed file never stops the batch; a batch with failures ends in *Finished with problems*.

### Help, welcome, settings

- [x] **AC-13** A "?" button is always visible and opens the help: how to use, supported formats, where results
  go, the privacy promise, how to change the language (in English and Spanish).
- [x] **AC-14** On first run a welcome in three steps appears, with "Don't show again" (setting `show_welcome`).
- [x] **AC-15** The settings window has exactly the settings of ADR-0012 (language, theme, open the folder when
  done, existing outputs, subfolders, HTML strategy, welcome), each with a one-line explanation, and
  **Restore defaults**; saving writes `settings.toml` atomically and the app applies it.

### Look and keyboard

- [x] **AC-16** Light and dark themes, following the system by default; the system theme is detected without
  extra dependencies (light when unknown).
- [x] **AC-17** Every margin, padding and gap is a multiple of 8 px (4 for tight pairs); body text is at least
  14 px; one primary action per screen.
- [x] **AC-18** Everything works with the keyboard: a logical tab order, Enter triggers the primary action, Esc
  closes dialogs.
- [x] **AC-19** Nothing is reachable only by hover.
- [x] **AC-22** The window wears ClearMD's identity (ADR-0027): the teal themes (light and dark), the rail with
  the logo, the name and the four steps with the current one highlighted, rounded cards and buttons, and the
  app icon as the window icon.
- [x] **AC-23** Every list (inputs, plan, result) shows the number, the file's own icon (by format; folders,
  Markdown and unknown files included) and its name; the icons and the logo are generated by ClearMD's own
  script and the committed files match it.

### Delivered

- [x] **AC-20** `clearmd-ttk` starts the GUI; a batch converted through the GUI gives the same outputs and summary
  as the CLI for the same inputs.
- [x] **AC-21** Screenshots of every screen, light and dark, English and Spanish, are generated by a script and
  committed in `docs/screenshots/005/`.

## Actors and data

- **Actors:** a non-technical user (first), any user of the CLI.
- **Data:** the same as feature 001; `settings.toml` is now also written.

## Risks / open questions

- **Tk on Windows high-DPI screens:** sizes are in pixels; the window scales with the system setting (to check
  on the packaged executable, 006).
- **tkinterdnd2's binaries** for each system: checked when the executables are built (006).
