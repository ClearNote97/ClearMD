# Feature 002 — `.tex` converter

## Goal

A LaTeX document — a paper, or a whole thesis split into chapters — becomes one readable Markdown file whose
equations render on GitHub and Obsidian, without pandoc and without leaving the machine; whatever could not be
converted faithfully is said, not hidden.

## Scope

- **Includes:**
  - An own converter for `.tex` on `pylatexenc` (ADR-0006), running in the worker process like markitdown's
    (ADR-0015), through the same pipeline, plan, limits and summary of feature 001.
  - The supported subset below; everything else is left as written and reported.
  - Following `\input` / `\include` / `\subfile` inside the document folder (ADR-0022).
  - Expanding the author's own macros, with limits (ADR-0022).
  - **Conversion notes**: a converter can report what it could not do faithfully; the summary and the CLI show it
    (ADR-0022). markitdown's converters report none.
  - Detection: the `.tex` extension, and magika's `latex` label for files without extension (ADR-0021).
  - Encoding: UTF-8, or the encoding declared with `inputenc`, or a detected one.
  - The benchmark gets a `.tex` case, so its speed and memory factors are measured, not guessed.
- **Does not include:** converting `.bib` bibliographies; rendering TikZ, PSTricks or other drawings; running
  LaTeX; `\def` with parameter patterns, conditionals and package internals (they are unknown commands); copying
  images (out of scope since feature 001); BibTeX-style numbering of equations, figures and citations.

## The supported subset

| LaTeX | Markdown |
|---|---|
| `\part`, `\chapter`, `\section`, `\subsection`, `\subsubsection`, `\paragraph` (starred too) | headings, one level per command present, starting at `##` under the title |
| `\title`, `\author`, `\date` + `\maketitle` | `# Title`, then one line with author and date |
| `abstract` environment | a "Resumen" or "Abstract" heading, by the document's `babel` language |
| `\textbf`, `\textit`, `\emph`, `\texttt`, `\underline` | `**…**`, `*…*`, `*…*`, `` `…` ``, `<u>…</u>` |
| `itemize`, `enumerate`, `description` (nested) | `-`, `1.`, `- **term** …` |
| `$…$`, `\(…\)` | `$…$` |
| `$$…$$`, `\[…\]`, `equation`, `equation*`, `displaymath` | `$$…$$` on its own lines |
| `align`, `align*`, `gather`, `gather*`, `multline`, `eqnarray` | `$$\begin{aligned}…\end{aligned}$$` (`gather` → `gathered`) |
| `verbatim`, `lstlisting`, `minted` | fenced code block, with the language when declared |
| `\verb|…|` | inline code |
| `\href{url}{text}`, `\url{url}` | `[text](url)`, `<url>` |
| `\footnote{…}` | `[^n]` with the note at the end |
| `quote`, `quotation`, `verse` | `>` block quote |
| `tabular` (and inside `table`) without `\multicolumn`/`\multirow` | a Markdown table; rules (`\hline`) dropped |
| `\includegraphics` (inside `figure` with `\caption` or not) | `![caption](path)`, the path relative to the output `.md` |
| `\caption` of a table | an italic line under the table |
| `\cite`, `\citep`, `\citet`, `\parencite`, `\textcite` | `[@key]`, `[@a; @b]` (pandoc citation syntax) |
| `\ref`, `\eqref`, `\autoref`, `\cref` | `(label)` |
| `\label`, `\index`, `\vspace`, `\hspace`, `\newpage`, `\clearpage`, `\noindent`, `\centering`, `\tableofcontents` | dropped (layout only) |
| accents and special characters (`\'a`, `\~n`, `\ss`, `~`, `--`, `---`, ``` `` '' ```) | Unicode |
| comments `%` | dropped |

## Acceptance criteria (what MUST be true)

Each criterion has an acceptance test named after its id (`tests/acceptance/test_002_tex_converter.py`).

### Through the pipeline

- [x] **AC-01** A `.tex` file converts through the CLI exactly like the formats of feature 001: into
  `ClearMD_Output/OutputMD/<name>.md`, listed in `Resumen_ClearMD.md` with format `TEX`, in cost order, under
  the worker's limits.
- [x] **AC-02** A LaTeX file without extension is detected by its content (magika `latex`) and converted.
- [x] **AC-03** The CLI process never imports `pylatexenc` (it runs in the worker, as markitdown does).

### Structure and text

- [x] **AC-04** Title, author and date from `\maketitle` become the `#` title and a line under it; sectioning
  commands become headings, the shallowest one present at `##`.
- [x] **AC-05** Emphasis, lists (nested), quotes, links, footnotes and code blocks follow the table above.
- [x] **AC-06** Accents and special characters become Unicode (`Nicol\'as` → `Nicolás`, `---` → `—`, `~` → a
  non-breaking space); comments and layout-only commands disappear.
- [x] **AC-07** `\cite{a,b}` becomes `[@a; @b]`; `\ref{eq:1}` becomes `(eq:1)`.
- [x] **AC-08** The `abstract` environment gets a "Resumen" heading in a document with `\usepackage[spanish]{babel}`
  and "Abstract" otherwise.

### Math

- [x] **AC-09** Inline and display math are kept as written (`$…$`, `$$…$$`); `\[…\]` and `equation` become
  `$$…$$`; `align`-like environments become `aligned` inside `$$…$$`.
- [x] **AC-10** Text inside math is never altered by text rules (no Unicode conversion, no escaping), except a
  backtick (it would pair with a code span of ClearMD's) and an HTML-looking `<tag` (ADR-0023).

### Tables and figures

- [x] **AC-11** A simple `tabular` becomes a Markdown table, its caption an italic line under it.
- [x] **AC-12** A table with `\multicolumn` or `\multirow` is kept as a LaTeX code block and reported as a note.
- [x] **AC-13** `\includegraphics{img/plot}` inside a figure becomes `![caption](…/img/plot.png)` with a path that
  works from the output `.md` (an existing file with a common image extension is looked up when the extension is
  omitted); a missing image keeps the path as written.

### Includes (ADR-0022)

- [x] **AC-14** `\input{chapters/ch1}` and `\include{…}` are replaced by the converted content of
  `chapters/ch1.tex`, recursively: a thesis converts into one Markdown file.
- [x] **AC-15** An include with an absolute path, a `..` segment, a link on the way, a non-`.tex` file, a missing
  file, a cycle, more than 8 levels or more than 200 files is not followed: a visible placeholder stays in the
  Markdown and a note names it with the reason. Nothing outside the document folder is ever read.

### Macros (ADR-0022)

- [x] **AC-16** The author's `\newcommand`/`\renewcommand`/`\providecommand` (up to 9 arguments, an optional
  first one with its default), `\DeclareMathOperator` and parameterless `\def` are expanded, in text and in math,
  including definitions made in an included file.
- [x] **AC-17** Expansion stops at 10,000 expansions (or 10 per KiB of source, when that is more), a nesting
  depth of 64, or an expanded text larger than 4×
  the source plus 1 MiB; what remains is left as written and a note says which limit was reached. A recursive or
  exponential macro never hangs or exhausts the worker.

### Honesty

- [x] **AC-18** Unknown commands and environments are left as written; the summary lists the file under
  "Converted with notes" with the distinct names (at most 20, then "and N more"), and the CLI prints one line for
  it. The exit code stays 0.
- [x] **AC-19** Notes are shown in the user's language (EN/ES) and are language-neutral data in the report.
- [x] **AC-20** A document in `latin1` (declared with `inputenc`, or not declared) converts with its accents; a
  guessed encoding is a note.

### Robustness

- [x] **AC-21** Malformed LaTeX (an unclosed group or environment, a stray `\end`) still produces Markdown for
  what could be parsed, with a note; it is never a crash.
- [x] **AC-22** The benchmark measures `.tex` (speed and memory per MiB) and `schemas/limits.py` uses the
  measured values.

## Actors and data

- **Actors:** the same as feature 001 (CLI now, GUIs later).
- **Data:** `.tex` files and the `.tex` files they include, read-only and only inside the document folder;
  referenced images are linked, never read or copied; an image named outside the folder or remote (`http:`,
  `//host`, an absolute path) is shown as code, never as a link, so opening the Markdown fetches nothing
  (ADR-0023).

## Risks / open questions

- **LaTeX is Turing-complete:** there will never be a 100% conversion; the subset and the notes are the contract.
- **pylatexenc's parsing of unusual input:** verified with fixtures, including hostile ones (unclosed groups,
  macro bombs, deep nesting).
- **Custom document classes** (university thesis classes) may define sectioning commands of their own: they are
  unknown commands unless defined with `\newcommand` in the document.
- **Speed:** pylatexenc reads a source character by character (measured in benchmark 002); a very large `.tex`
  meets the per-file time limit of ADR-0015 like any slow format.
- **Known limits of the subset** (from the review, accepted): a `\renewcommand` in the middle of a document
  applies to the whole document; a remote image the author wanted shows as code; `\date{\today}` gives no date;
  includes written by a macro are not followed (noted).
