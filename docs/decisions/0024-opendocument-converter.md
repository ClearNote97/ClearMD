# ADR-0024: OpenDocument text — XML read safely, images as placeholders, formulas as LaTeX

- **Status:** proposed
- **Date:** 2026-10-25
- **Refines:** ADR-0006 (the `.odt` converter).

## Context

ADR-0006 decided an own `.odt` converter with the standard library only (`zipfile` + XML over `content.xml`).
It did not say how to read untrusted XML, what to do with what Markdown cannot hold (images stored inside the
file, LibreOffice Math formulas, comments and tracked changes), nor whether the output guarantee built for
LaTeX (ADR-0023) applies. An `.odt` is a ZIP of XML files written by whoever made the document: the same
threats as any ZIP-based format (feature 001) plus XML's own (entity expansion, deep nesting, huge text).

## Decision

### Reading

- **Only `.odt`** (LibreOffice Writer). The `mimetype` entry must be `application/vnd.oasis.opendocument.text`;
  another OpenDocument type is "unsupported format". An encrypted `content.xml` (declared in
  `META-INF/manifest.xml`) is "password-protected", as for PDF.
- The archive goes through the ZIP check of feature 001 before anything is read (ODT joins `ZIP_BASED`).
- **XML with `pyexpat`, not `xml.etree`:** the parser builds a minimal tree of its own so that ClearMD decides
  the limits. Any `DOCTYPE` or entity declaration refuses the file (ODF never uses them; this closes entity
  expansion whatever the expat version). Limits per XML part: elements, nesting depth and characters, fixed in
  `limits` like the other safety limits (ADR-0012). The tree is walked without recursion.
- Styles are resolved from `content.xml`'s automatic styles and `styles.xml`'s named styles, with their parent
  chain: bold, italic, underline, strike-through, superscript/subscript, monospace; paragraph styles for title,
  subtitle, quotations and preformatted text.

### What Markdown cannot hold

- **Images stay inside the `.odt`:** each one becomes an italic placeholder with its title or description
  (`*Image: Map of the region*`) and a note counts them. ClearMD still never writes files other than the
  Markdown and the summary (feature 001).
- **Formulas (LibreOffice Math objects) become LaTeX:** their MathML is converted to `$…$`, or `$$…$$` when
  the formula is alone in its paragraph, for a defined subset (fractions, roots, scripts, Greek letters,
  operators with limits, fences, accents, simple matrices, text). A formula outside the subset is shown as
  its StarMath source in inline code, with a note.
- **Comments and tracked changes:** the text is the final one (changes accepted, comments removed), and a note
  says the document had them.
- **Merged table cells:** Markdown has none; the content stays in the first cell, the covered ones are empty,
  and a note says the table was simplified.
- Anything else ClearMD does not know keeps its text and is listed in a note.

### Output

- **The output guarantee of ADR-0023 applies to every converter ClearMD writes:** the code that escapes
  document text, marks ClearMD's own block lines and neutralizes the rest moves out of the LaTeX package into a
  shared module, and the `.odt` converter uses it. The CommonMark-parser test and the fuzz get an `.odt` corpus.

## Consequences

- **Gains:** no dependency; every limit is ClearMD's, not a library default; formulas render on GitHub and
  Obsidian as in feature 002; one guarantee for both own converters.
- **Costs:** a small XML tree builder and a MathML-to-LaTeX translator to maintain; images are not visible in
  the Markdown.

## Alternatives considered

- **`xml.etree` / `xml.dom.minidom`:** no hook to refuse a `DOCTYPE` before it is processed; safe only with a
  recent expat. Rejected for untrusted input.
- **`defusedxml`:** the right tool, but a dependency, against ADR-0006.
- **`odfpy`:** rejected by ADR-0006 (last release 2020, no license declared).
- **Extracting images:** more useful, but new writes, new limits and a new section of the summary; out of the
  scope kept since feature 001 (the user chose the placeholder).
- **StarMath source only, or dropping formulas:** simpler, but equations would not render.
