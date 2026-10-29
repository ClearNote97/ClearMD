# ADR-0032: A light executable: ClearMD's own detection and Excel converter, two languages of babel

- **Status:** accepted
- **Date:** 2026-10-29
- **Refines:** ADR-0010 (content detection by magika), ADR-0004 (markitdown for Excel),
  ADR-0028 (the executables).

## Context

The author found v0.1.0's executable heavy (about 95 MB). Three libraries were most of it, and
each did a small job:

| Library | Size installed | Its job in ClearMD |
|---|---|---|
| onnxruntime (with magika) | 66 MB | Detecting the format of a file **without an extension** |
| pandas and numpy | about 100 MB | Reading `.xlsx` into a table, inside markitdown |
| babel's language data | 33 MB | Imported by trafilatura's URL filter, for one language check ClearMD does not use |

## Decision

- **Own content detection by signatures** (`detection/content.py`). It still runs only for files
  without an extension (ADR-0010). It reads the first 64 KiB, and for a ZIP the names of its
  entries:
  - a PDF header with objects;
  - the parts of docx, pptx and xlsx;
  - the `mimetype` of ODT and EPUB;
  - an HTML start, a notebook's keys, LaTeX commands, a CSV's steady delimiters, plain text.

  A program (shebang, imports) or anything else is "unsupported", as before.
- **Own Excel converter** with openpyxl (already a dependency of markitdown's xlsx path), read
  only, with each formula's last value. Each sheet is a heading and a table, as markitdown wrote
  it, every cell escaped (ADR-0023).
- **The executables leave out** magika, onnxruntime, numpy and pandas.
  - markitdown imports magika when it loads but only uses it in `MarkItDown()`, which ClearMD never
    builds: a PyInstaller runtime hook provides an empty stand-in.
  - babel keeps only its root, English and Spanish data.
  - The notices list only what ships.

## Consequences

- The executable goes from about 90 MB to about 41 MB (Linux), checked by the same real batch.
- Development installs still bring magika and pandas through markitdown. Only the executables are
  light.
- Detection by signatures recognises the formats ClearMD converts and nothing more. A file
  without an extension whose content matches none of them is "unsupported".
