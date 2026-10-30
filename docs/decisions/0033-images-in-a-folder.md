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
  - chosen on step 1, at the right of the output card's title ("Images: Leave out · In a
    folder"), so the list keeps its rows in the smallest window;
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
  - The ones left out are counted in a note: past a limit, in another format, or a data link
    no image took (cut to its kind, as markitdown does when images are off).
  - The folder's name is encoded in the links where it would end them: `#`, `%`, `?`.
- **Where the pictures come from:**

  | Format | Source |
  |---|---|
  | docx, pptx | markitdown gives them as `data:` URIs (`keep_data_uris`), made files by the sink (an alt with `]`, a title: still found) |
  | EPUB | read from its package by the entry whose path ends most like the link (a tie: left as it was), each read once |
  | ODT | read from its `Pictures/`, through the same safe part reader, each read once |
  | PDF | PDFium's image objects (in form objects too), decoded at their own size (never at the size they are drawn), at most 40 million pixels each and 400 million per document, placed in the page's reading order; never taken for a running header |
- **Only the interface's process writes files.** The worker sends the images with the Markdown,
  and they are written as the Markdown is:
  - before the Markdown: a folder that cannot be written leaves the earlier Markdown as it was;
  - inside the output root, never through a link;
  - every name checked first: a name other than ClearMD's own is refused before anything changes;
  - the folder's earlier `image-NNN` files that are not written again go; a folder left empty too.
- HTML pages and LaTeX keep their pictures as before (never downloaded, never copied from disk).

## Consequences

- Documents keep their pictures, viewable next to the Markdown.
- More bytes cross from the worker to the interface (up to 200 MB per document).
- The planner's memory estimate does not grow with images on: a docx's pictures, held as base64
  by markitdown, can take more (review of 012, R12-13); a picture is never decoded past its limit.
- Equations of a PDF (feature 013) can use the same folder.
