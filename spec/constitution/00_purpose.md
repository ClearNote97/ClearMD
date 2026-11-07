<!--
====================================================================
 00 — PURPOSE  ·  Level 1 (Constitution)
--------------------------------------------------------------------
 Per-project. Sets the ground against which scope (02), principles (01)
 and stack (03) are justified. Validated with the author on 2026-10-24.
====================================================================
-->

# 00 — Purpose

## Mission

Anyone can prepare their documents for AI **without uploading them anywhere**, with a desktop app they
download and simply use. It **converts** them to clean Markdown, **splits** a large file into parts that fit,
and **merges** several files into one (ADR-0043, from version 2).

## Problem

- Useful content is trapped in heavy formats (PDF, Word, PowerPoint, LaTeX, LibreOffice), while it is needed
  in Markdown: for notes (Obsidian, wikis), for documentation on GitHub, and as context for LLMs.
- Existing tools are command-line libraries (markitdown, pandoc), web services that require uploading the
  document, or single-format converters. None of them is made for someone who never opens a terminal.
- LaTeX in particular has no pure-Python path to Markdown: the usual answer is pandoc, an external binary.

## For whom

ClearMD is for everyone who needs Markdown from documents:

- students and academics (theses and papers in LaTeX or Word);
- people preparing documents as context for LLMs;
- developers, who use the CLI in scripts and pipelines;
- **non-technical users — the primary persona.** Everything must be foolproof: if it works for someone who
  has never opened a terminal, it works for everyone (ADR-0013).

The author decides and maintains it (personal, public portfolio project). Nobody pays: it is free software
(MIT). No accounts, no multi-tenancy.

## Success metrics

- A mixed folder (pdf, docx, pptx, xlsx, tex, odt, html) converts in one step into `ClearMD_Output`, with a
  `Resumen_ClearMD.md` of what was converted, skipped and failed, and no unhandled error.
- Executables for Windows and Linux, built by CI and published in GitHub Releases, run without installing
  Python.
- The same functionality in the CLI, ttkbootstrap, PySide6 and flet, on a single core.
- The size of every executable is measured in CI and reported, so the toolkits can be compared.

---

> `02_scope` draws the borders of this purpose, `01_principles` sets how it is pursued and `03_stack` with what.
