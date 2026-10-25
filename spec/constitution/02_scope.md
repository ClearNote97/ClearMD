<!--
====================================================================
 02 — SCOPE  ·  Level 1 (Constitution)
--------------------------------------------------------------------
 Per-project. The most valuable part is not what goes in, but what is
 deliberately left OUT. Validated with the author on 2026-10-24.
====================================================================
-->

# 02 — Scope

## In scope

- **Convert to Markdown** PDF, docx, pptx, xlsx, HTML, CSV, EPUB and Jupyter notebooks (through markitdown,
  ADR-0004).
- **Convert LaTeX (`.tex`)** keeping the math, over a subset defined in its spec (ADR-0006).
- **Convert OpenDocument (`.odt`)** with no external dependency (ADR-0006).
- **Extract only the article** from an HTML file, as an alternative strategy to the full page (ADR-0006).
- **Convert in batches:** several files and/or whole folders, recursively (ADR-0010).
- **Detect the format** of each file even when the extension is missing (ADR-0010).
- **Write the results into `ClearMD_Output/Output/`** next to the input or in a folder the user chooses, with a
  `Resumen_ClearMD.md` per output folder: a name table and the history of earlier batches (ADR-0016).
- **Convert safely and responsively:** a worker process with time, memory and archive limits, real
  cancellation, and the cheapest files first (ADR-0015).
- **Speak English and Spanish**, English by default, switchable in the settings (ADR-0012, ADR-0017).
- **Remember preferences** in one settings file shared by every interface, editable from a settings window
  (ADR-0012).
- **Guide the user:** "?" help window, first-run welcome, visible state and progress, human error messages
  (ADR-0013, `spec/contracts/ux.md`).
- **Offer four interfaces** on the same core: CLI, ttkbootstrap, PySide6 and flet (ADR-0001).
- **Ship executables** for Windows and Linux from GitHub Actions (ADR-0008).

## Out of scope — explicit

- **Anything that uses the network or the cloud:** URLs, audio transcription, YouTube, Azure, image
  descriptions with an LLM. It breaks the privacy promise (ADR-0005).
- **OCR of scanned PDFs:** needs heavy models or services; maybe later, as a local option.
- **ZIP archives:** a ZIP can hide a zip bomb, and its contents are better converted as a folder. markitdown's
  ZIP converter is not used.
- **Extracting embedded images** from documents: v1 converts text and structure.
- **Reverse conversion** (Markdown → docx/pdf): a different product.
- **Editing the resulting Markdown inside the app:** editors already do that.
- **A database or a searchable history** (ADR-0002).
- **A macOS executable:** notarization requires a paid Apple Developer account (ADR-0008).
- **Minor formats** (`.rtf`, `.eml`, subtitles): on the roadmap, not in v1.
- **Other summary formats** (e.g. PDF): a possible option later; v1 writes Markdown only.

## Assumptions

- Input documents fit in the memory of an ordinary desktop computer.
- markitdown stays maintained; if not, the `DocumentConverter` port allows replacing it.

## Constraints

- **Privacy:** ClearMD never uses the internet. If the results are saved in a folder synced by OneDrive,
  Google Drive or Dropbox, that app may upload them — that is the sync app, not ClearMD.
- **Licenses:** every dependency must allow distributing an MIT app (ADR-0003).
- **Budget:** zero. No paid services, no paid code signing (for now).

## System boundaries

- **Local file system:** the only input and output. ClearMD writes only inside `ClearMD_Output` and its
  settings file.
- **Worker process:** a child process of ClearMD itself, on the same machine (ADR-0015).
- **markitdown:** an external dependency hidden behind `DocumentConverter`.
- **GitHub Actions / Releases:** only to build and publish executables; the app never talks to GitHub.
