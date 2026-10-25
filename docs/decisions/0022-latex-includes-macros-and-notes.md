# ADR-0022: LaTeX — following includes, expanding the author's macros, and honest conversion notes

- **Status:** accepted; includes, images and robustness refined by ADR-0023
- **Date:** 2026-10-25
- **Refines:** ADR-0006 (the `.tex` converter).

## Context

Real theses are split into a main file and chapters (`\input{chapters/ch1}`), define their own macros
(`\newcommand{\R}{\mathbb{R}}`, mostly inside equations) and use commands no converter can know. ADR-0006 said
"anything unknown is left as is and reported", but not how, nor what to do with includes and macros. Both
features read or grow content under an attacker's control: an `\input{/etc/passwd}` or `\input{../../secret}`
must not leak files into the Markdown, and macros can recurse or grow exponentially (`\def\a{\b\b}`
`\def\b{\c\c}`…), the LaTeX equivalent of a zip bomb.

## Decision

### Includes (`\input`, `\include`, `\subfile`)

- Followed **only inside the folder of the file being converted** (the "document folder"): relative paths only;
  no absolute paths, no `..` segment, no symbolic link or junction on the way; `.tex` is added when the name has
  no extension, and only `.tex` files are read.
- Cycles are detected; nesting depth is at most **8**; a document reads at most **200** included files and, in
  total, no more than the file-size limit of ADR-0010 (250 MiB).
- An include that is not followed (outside the folder, missing, a cycle, over a limit) is left as a visible
  placeholder and reported as a note.
- In a folder batch, the chapter files are still converted on their own too: simple and predictable.

### The author's macros

- Expanded: `\newcommand`, `\renewcommand`, `\providecommand` (with up to 9 arguments and an optional first
  argument with its default), `\DeclareMathOperator` (→ `\operatorname{…}`), and `\def` **without parameters**.
- Not expanded: `\def` with parameter patterns, `\let`, conditionals, `\makeatletter` internals, macros from
  packages and classes (`.sty`, `.cls`): they are unknown commands.
- Limits per document: at most **10,000 expansions, or 10 per KiB of source when that is more** (benchmark 002: a
  1 MiB thesis that uses its macros in every equation needs more than 10,000; growth and nesting are what stop a
  bomb), nesting depth at most **64**, and the expanded text at most **4× the size of the source plus 1 MiB**. When a limit is reached, expansion stops, what remains is left as
  written, and a note says so. The limits are fixed (not settings), like the other safety limits (ADR-0012).

### Conversion notes

- A converter returns the Markdown **and notes**: structured, language-neutral facts about what it could not do
  faithfully (unknown commands, includes not followed, a macro limit reached, a table simplified, an encoding
  guessed). The summary lists them under **"Converted with notes"** in the user's language; the CLI shows one line.
- A file with notes is still converted (exit code 0): notes are honesty, not failure. The same mechanism serves
  `.odt` (feature 003) and any later converter.

## Consequences

- **Gains:** a whole thesis becomes one Markdown file, ready for an LLM; equations with the author's macros render
  on GitHub and Obsidian; the user is told exactly what was not converted faithfully.
- **Costs:** a macro expander and an include resolver to maintain and test against hostile input; notes widen the
  contract between converters, the worker protocol and the summary.

## Alternatives considered

- **Not following includes:** rejected; a thesis would come out as a skeleton.
- **Following includes anywhere:** rejected; a document could pull any readable file into the output.
- **Leaving macros unexpanded:** rejected; most custom math would not render.
- **Silently dropping unknown commands:** rejected; it hides what was lost.
