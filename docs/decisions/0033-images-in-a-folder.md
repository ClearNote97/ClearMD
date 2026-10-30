# ADR-0033: A document's images in a folder next to its Markdown

- **Status:** accepted
- **Date:** 2026-10-30
- **Refines:** ADR-0023 (the Markdown writes no link but ClearMD's own) and the converters' image
  placeholders (ADR-0024, ADR-0030).

## Context

Until now a document's pictures became a placeholder (ODT), a broken link (pptx), a truncated
`data:` text (docx), or nothing (PDF). The author asked to keep them, optionally, in a folder named
like the document with the suffix `_images` (`_imagenes` in Spanish), chosen when converting and
remembered in Settings.

## Decision

- **A setting, `images` = `omit` (default) or `folder`**:
  - chosen on step 1, on the summary's row ("Images: Leave out · In a folder");
  - in Settings;
  - `--images` / `--no-images` on the command line.
- **The folder** is `<Markdown name>_images` (or `_imagenes` when the app is in Spanish, at
  conversion time), next to the Markdown. The links are relative: `report_images/image-001.png`.
- **An `ImageSink` in the worker** takes each picture's bytes from the converter, and names it
  `image-001.png` (never a name from the document).
  - It keeps only the pictures a Markdown viewer shows, recognised by their bytes: PNG, JPEG,
    GIF, BMP, WebP.
  - A picture used again is kept once.
  - Limits: 1,000 pictures, 50 MB each, 200 MB per document.
  - The ones left out are counted in a note.
- **Where the pictures come from:**

  | Format | Source |
  |---|---|
  | docx, pptx | markitdown gives them as `data:` URIs (`keep_data_uris`), made files by the sink |
  | EPUB | read from its package by the name its chapters link |
  | ODT | read from its `Pictures/`, through the same safe part reader |
  | PDF | PDFium's image objects, rendered to PNG (at most 40 million pixels) and placed in the page's reading order |
- **Only the interface's process writes files.** The worker sends the images with the Markdown,
  and they are written as the Markdown is:
  - inside the output root, never through a link;
  - the folder's earlier `image-NNN` files go first;
  - a name other than ClearMD's own is refused.
- HTML pages and LaTeX keep their pictures as before (never downloaded, never copied from disk).

## Consequences

- Documents keep their pictures, viewable next to the Markdown.
- More bytes cross from the worker to the interface (up to 200 MB per document).
- Equations of a PDF (feature 013) can use the same folder.
