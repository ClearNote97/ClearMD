# ADR-0006: Own converters — .tex, .odt and HTML article mode

- **Status:** accepted
- **Date:** 2026-10-24

## Context

markitdown does not convert LaTeX or OpenDocument, and its HTML conversion includes all of the page content
(menus, footers, ads). These are the gaps where ClearMD can contribute something of its own (ADR-0004).

## Decision

### `.tex` (LaTeX) — the main feature

- Parser: **`pylatexenc`** (MIT, 2.11) builds the document tree; an own *visitor* walks it and emits
  Markdown.
- Math is **kept as is** (`$...$`, `$$...$$`; `\[...\]` and `equation` become `$$...$$`):
  GitHub, Obsidian and VS Code already render it in Markdown.
- The structure is converted: sections, emphasis, lists, links, code blocks (`verbatim`,
  `lstlisting`), citations (`\cite{x}` → `[@x]`) and simple tables.
- LaTeX is a Turing-complete macro language: there will never be a 100% conversion. The feature spec defines
  the **supported subset**; anything unknown is left as is and reported.

### `.odt` (OpenDocument / LibreOffice)

- Standard library only: `zipfile` + `xml.etree.ElementTree` over `content.xml`. **Zero dependencies.**
- Relevant in Latin America, where LibreOffice is common in the public sector and in education.

### HTML "article mode"

- A second strategy for the same format: **`trafilatura`** (Apache-2.0, 2.3.1) extracts only the main
  content. The user chooses between "full page" (markitdown) and "article only".
- It shows the Strategy pattern: same input format, two interchangeable strategies.

## Consequences

- **Gains:** a real differentiator (LaTeX → Markdown without pandoc); a dependency-free converter that demonstrates
  the port; a clear example of interchangeable strategies.
- **Costs:** the `.tex` converter needs a careful spec and many fixtures; `trafilatura` brings several
  dependencies (lxml, among others).

## Alternatives considered

- **Pandoc for `.tex`:** it converts better, but it is a ~100 MB Haskell binary under the GPL license. It breaks the
  "full Python" approach, bloats the executable and complicates the distribution's licensing. Rejected.
- **`TexSoup` as the parser:** viable (BSD), but `pylatexenc` is better maintained.
- **`odfpy` for `.odt`:** its latest version is from 2020 and it declares no license on PyPI. Rejected.
- **An own HTML converter that repeats what markitdown does:** no added value. Rejected.
