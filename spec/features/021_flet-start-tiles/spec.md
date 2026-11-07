# Feature 021 — flet's empty list as two large tiles; titles in Title Case

## Goal

flet 1.0 cannot receive files dropped from the system, so the flet window's empty list was a large
frame with one sentence in it: room that did nothing. Before anything is chosen, that room now holds
two large tiles, **Add Files** and **Add Folder**, each with an icon and what it takes, and a hint
under them (ADR-0042, amended). The ttk and Qt windows keep their drop zone.

## Scope

- **Includes:** the tiles on step 1 of the flet window; their texts in English and Spanish; the
  windows' titles in Title Case (the owner's rule, already the installer's).
- **Does not include:** dropping files on the flet window (it needs a Flutter client built for it:
  `flet build` with an extension); the ttk and Qt windows.

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_021_*.py`).

- [x] **AC-01** With nothing listed, step 1 shows the two tiles, each with an icon, its title and
  what it takes, and a hint; the small buttons, the empty list and its links are not shown.
- [x] **AC-02** Each tile does what its small button does: it opens its picker, and what is chosen
  is listed.
- [x] **AC-03** Once something is listed, the tiles give way to the small buttons, the list and its
  links; when the list is emptied, the tiles come back.
- [x] **AC-04** The tiles are enabled and disabled with the small buttons.
- [x] **AC-05** Their texts in English and Spanish; the sentence that sent people to the two buttons
  is gone from the catalogs.
- [x] **AC-06** Every title of the three windows (pages, cards, dialogs, columns, figures, settings,
  the tiles), every button, and the headings of the summary (Markdown and PDF) are in Title Case
  in both languages: each word capitalised but the connectors, the first
  word always; brands keep their own form.
