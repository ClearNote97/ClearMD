# UX contract — shared by every ClearMD interface

> **Prescriptive.** Every GUI (ttkbootstrap, PySide6, flet) must satisfy this contract; the CLI satisfies the
> parts marked *(CLI too)*. Rationale: ADR-0013. Messages come from the catalogs of ADR-0012.

## 1. The user always knows what is happening

- **One visible state at all times:** *Ready* · *Analyzing* · *Waiting for your decision* · *Converting* ·
  *Finished* · *Finished with problems* · *Cancelled*. *(CLI too: as text.)*
- **Progress:** while converting, show "*i* of *n*", the current file name and a progress bar. Anything that
  takes longer than ~300 ms shows a busy indicator. *(CLI too: "[3/37] report.pdf".)*
- **Startup:** if opening the app takes noticeably long (packaged executables unpack first), show a splash or
  loading screen instead of nothing.
- **The window never freezes:** conversions run outside the UI thread (ADR-0001). A **Cancel** button is
  always available while a batch runs.

## 2. Nothing surprising happens to the user's files

- Before converting, show the **batch plan**: how many files will be converted, which ones are skipped and
  why, and which outputs already exist. The user confirms. *(CLI too: summary + prompt or flags.)*
- Never overwrite silently (ADR-0010). Never write outside `ClearMD_Output`.
- When the batch ends: a summary (converted / skipped / failed), a button **Open results folder**, and — by
  default — the folder opens by itself (setting, ADR-0012).

## 3. Errors speak human

- Every error shows **what happened, in plain words, and what to do**: "This PDF is password-protected.
  Remove the password and try again." Never a traceback, an exception name or an error code alone.
  *(CLI too.)*
- Technical details (exception, stack) go to the batch report, under each failed file.
- One failed file never stops the batch.

## 4. Help is one click away

- A **"?" button** is always visible and opens the instructions window (how to use, supported formats,
  where results go, privacy promise).
- On first run, a **welcome** in three steps: *1. Choose files or a folder → 2. Review what will be converted →
  3. Done, your folder opens.* It has "Don't show again" (setting `show_welcome`).
- Nothing is reachable **only** by hover: tooltips may repeat information, never be its only source.

## 5. Layout and visual rhythm

- **Spacing grid of 8 px:** every margin, padding and gap is a multiple of 8 (4 allowed for tight inline
  pairs). Equal elements get equal spacing: the layout is symmetric unless there is a reason.
- One primary action per screen, visually dominant (e.g. **Convert**); secondary actions look secondary.
- Two entry actions side by side: **Add files** and **Add folder** (native dialogs cannot mix both, ADR-0010),
  plus drag and drop where the toolkit allows it.
- Minimum body text 14 px (or the toolkit's equivalent); contrast meets WCAG AA (4.5:1 for text).
- Light and dark themes, following the system by default.

## 6. Keyboard and accessibility

- Everything works with the keyboard: logical tab order, visible focus, Enter triggers the primary action,
  Esc closes dialogs.
- Controls have accessible names (where the toolkit exposes them).

## 7. Settings window

Exactly the settings of ADR-0012, each with a one-line explanation, plus **Restore defaults**. The app must
work perfectly without ever opening this window.
