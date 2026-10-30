# Feature 012 — Images in a folder

## Goal

A document's pictures, kept on request in a folder next to its Markdown and linked from it
(ADR-0033).

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test (`tests/acceptance/test_012_images_in_a_folder.py`).

- [ ] **AC-01** With images in a folder, a document's pictures are written to `<name>_images` next
  to its Markdown (`_imagenes` in Spanish) and linked from it, for docx, pptx, EPUB, ODT and PDF.
- [ ] **AC-02** By default (and with `--no-images`) no picture is written: the Markdown is as
  before.
- [ ] **AC-03** Pictures are named by ClearMD, recognised by their bytes, kept once, within limits;
  those left out are told in the summary.
- [ ] **AC-04** The images folder is written like the Markdown: inside the output, never through a
  link, its earlier pictures replaced.
- [ ] **AC-05** The choice is on step 1 (on the summary's row) and in Settings, remembered; the
  command line has `--images` / `--no-images`; English and Spanish; screenshots in
  `docs/screenshots/012/`.
