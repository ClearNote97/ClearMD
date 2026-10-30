# Feature 012 — Images in a folder

## Goal

A document's pictures, kept on request in a folder next to its Markdown and linked from it
(ADR-0033).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_012_images_in_a_folder.py`).

- [x] **AC-01** With images in a folder, a document's pictures are written to `<name>_images` next
  to its Markdown (`_imagenes` in Spanish) and linked from it, for docx, pptx, EPUB, ODT and PDF.
- [x] **AC-02** By default (and with `--no-images`) no picture is written: the Markdown is as
  before.
- [x] **AC-03** Pictures are named by ClearMD, recognised by their bytes, kept once, within limits;
  those left out are told in the summary.
- [x] **AC-04** The images folder is written like the Markdown: inside the output, never through a
  link, its earlier pictures replaced.
- [x] **AC-05** The choice is on step 1 (at the right of the output's title, fitting 800 px in
  Spanish) and in Settings, remembered; the
  command line has `--images` / `--no-images`; English and Spanish; screenshots in
  `docs/screenshots/012/`.
