"""The supported subset of spec 002, row by row (AC-04 - AC-13, AC-18, AC-21)."""

from pathlib import Path

import pytest
from support import TEX_DIR

from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.conversion.tex.render import render_latex


def md(latex: str) -> str:
    return render_latex(latex).markdown


def notes(latex: str) -> tuple[ConversionNote, ...]:
    return render_latex(latex).notes


def doc(body: str, preamble: str = "") -> str:
    return f"\\documentclass{{article}}{preamble}\\begin{{document}}{body}\\end{{document}}"


# --- Structure -----------------------------------------------------------------------------------


def test_title_author_and_date_become_the_title_block() -> None:
    text = md(doc("\\maketitle Hola.", "\\title{Mi tesis}\\author{Ana \\and Luis}\\date{2026}"))
    assert text.startswith("# Mi tesis\n\n*Ana, Luis · 2026*\n\nHola.")


def test_the_shallowest_sectioning_command_is_level_two() -> None:
    text = md(doc("\\section{Uno}a\\subsection{Dos}b\\subsubsection*{Tres}c"))
    assert "## Uno" in text and "### Dos" in text and "#### Tres" in text


def test_chapters_push_sections_one_level_down() -> None:
    text = md(doc("\\chapter{Cap}\\section{Sec}"))
    assert "## Cap" in text and "### Sec" in text


@pytest.mark.parametrize(
    ("latex", "expected"),
    [
        ("\\textbf{b}", "**b**"),
        ("\\textit{i}", "*i*"),
        ("\\emph{e}", "*e*"),
        ("\\texttt{c}", "`c`"),
        ("\\underline{u}", "<u>u</u>"),
        ("\\textbf{\\emph{anidado}}", "***anidado***"),
    ],
)
def test_emphasis(latex: str, expected: str) -> None:
    assert md(doc(latex)).strip() == expected


def test_lists_nested_numbered_and_described() -> None:
    latex = doc(
        "\\begin{itemize}\\item uno\\item dos\\begin{enumerate}\\item a\\item b\\end{enumerate}"
        "\\end{itemize}\\begin{description}\\item[Término] definición\\end{description}"
    )
    lines = [line for line in md(latex).splitlines() if line.strip()]
    assert lines == ["- uno", "- dos", "  1. a", "  2. b", "- **Término** definición"]


def test_quotes_links_and_footnotes() -> None:
    text = md(
        doc(
            "\\begin{quote}Una cita.\\end{quote}\\href{https://example.org}{un enlace} y "
            "\\url{https://example.org/b}.\\footnote{Una nota.}"
        )
    )
    assert "> Una cita." in text
    assert "[un enlace](https://example.org)" in text
    assert "<https://example.org/b>" in text
    assert text.rstrip().endswith("[^1]: Una nota.")
    assert ".[^1]" in text


def test_code_blocks_keep_their_content_and_language() -> None:
    text = md(
        doc(
            '\\begin{lstlisting}[language=Python]\nx = "$a$ \\section{no}"\n\\end{lstlisting}'
            "\\begin{verbatim}\nraw -- text\n\\end{verbatim}"
            "\\begin{minted}{rust}\nfn main() {}\n\\end{minted} y \\verb|\\foo $x$|"
        )
    )
    assert '```python\nx = "$a$ \\section{no}"\n```' in text
    assert "```\nraw -- text\n```" in text
    assert "```rust\nfn main() {}\n```" in text
    assert "`\\foo $x$`" in text


def test_accents_and_special_characters_become_unicode() -> None:
    text = md(doc("Nicol\\'as Pe\\~na, \\ss{}, 1--2 --- ``hola'' a~b \\& \\% \\ldots"))
    assert "Nicolás Peña, ß, 1–2 — “hola” a\u00a0b & % …" in text


def test_comments_and_layout_only_commands_disappear() -> None:
    text = md(doc("a % oculto\n\\newpage\\noindent\\vspace{1cm}\\label{x}b"))
    assert "oculto" not in text and "vspace" not in text and "label" not in text
    assert "a" in text and "b" in text


def test_citations_and_references() -> None:
    text = md(doc("\\cite{knuth84,lamport94} \\citep{a} \\ref{eq:1} \\eqref{eq:2}"))
    assert "[@knuth84; @lamport94]" in text
    assert "[@a]" in text
    assert "(eq:1)" in text and "(eq:2)" in text


@pytest.mark.parametrize(
    ("preamble", "heading"),
    [("\\usepackage[spanish]{babel}", "## Resumen"), ("", "## Abstract")],
)
def test_the_abstract_heading_follows_the_documents_language(preamble: str, heading: str) -> None:
    text = md(doc("\\begin{abstract}Texto.\\end{abstract}", preamble))
    assert f"{heading}\n\nTexto." in text


# --- Math ----------------------------------------------------------------------------------------


def test_inline_and_display_math() -> None:
    text = md(
        doc(
            "$E=mc^2$ y \\(a+b\\). \\[ \\int_0^1 x\\,dx \\]"
            "\\begin{equation}\\label{eq:1} a^2+b^2=c^2 \\end{equation}"
            "\\begin{align} x &= 1 \\\\ y &= 2 \\end{align}"
        )
    )
    assert "$E=mc^2$ y $a+b$." in text
    assert "$$\n\\int_0^1 x\\,dx\n$$" in text
    assert "$$\na^2+b^2=c^2\n$$" in text
    assert "$$\n\\begin{aligned}\nx &= 1 \\\\ y &= 2\n\\end{aligned}\n$$" in text


def test_text_inside_math_is_never_touched() -> None:
    # Only a backtick is escaped: it would pair with a code span of ClearMD's (ADR-0023).
    assert "$a--b \\`\\`x'' \\%$" in md(doc("$a--b ``x'' \\%$"))
    assert "$a--b \\%$" in md(doc("$a--b \\%$"))


# --- Tables and figures --------------------------------------------------------------------------


def test_a_simple_table_becomes_markdown_with_its_caption() -> None:
    text = md(
        doc(
            "\\begin{table}\\begin{tabular}{|l|c|}\\hline A & B \\\\ \\hline 1 & $x$ \\\\ \\hline"
            "\\end{tabular}\\caption{Una tabla}\\end{table}"
        )
    )
    assert "| A | B |\n|---|---|\n| 1 | $x$ |" in text
    assert "*Una tabla*" in text


def test_a_table_with_merged_cells_is_kept_as_latex_and_noted() -> None:
    result = render_latex((TEX_DIR / "multicolumn.tex").read_text(encoding="utf-8"))
    assert "```latex\n\\begin{tabular}" in result.markdown
    assert ConversionNote(NoteKind.TABLE_KEPT_AS_LATEX, (NoteItem("1"),)) in result.notes


def test_a_figure_links_its_image_with_the_caption() -> None:
    text = md(
        doc(
            "\\begin{figure}\\includegraphics[width=3cm]{img/plot}"
            "\\caption{Un gráfico}\\end{figure}"
        )
    )
    assert "![Un gráfico](img/plot)" in text


# --- Honesty and robustness ----------------------------------------------------------------------


def test_unknown_commands_and_environments_are_kept_and_noted() -> None:
    result = render_latex((TEX_DIR / "unknown.tex").read_text(encoding="utf-8"))
    assert "\\customcommand{x}" in result.markdown
    assert "\\begin{weirdenv}dentro\\end{weirdenv}" in result.markdown
    (note,) = [n for n in result.notes if n.kind is NoteKind.UNKNOWN_COMMANDS]
    assert [item.subject for item in note.items] == [
        "\\customcommand",
        "\\otherthing",
        "\\begin{weirdenv}",
    ]


def test_malformed_latex_still_converts_with_a_note() -> None:
    result = render_latex((TEX_DIR / "malformed.tex").read_text(encoding="utf-8"))
    assert "fixture-tex-malformed" in result.markdown
    assert any(note.kind is NoteKind.PARSE_RECOVERED for note in result.notes)


def test_a_file_without_document_environment_is_rendered_whole() -> None:
    assert md("\\section{Capítulo suelto}Texto.").startswith("## Capítulo suelto\n\nTexto.")


def test_the_whole_paper_converts_without_unknown_commands() -> None:
    result = render_latex((TEX_DIR / "paper.tex").read_text(encoding="utf-8"))
    assert "fixture-tex-paper" in result.markdown
    assert [n for n in result.notes if n.kind is NoteKind.UNKNOWN_COMMANDS] == []


def test_the_paper_comes_out_exactly_as_expected() -> None:
    """The whole fixture, line by line: any change in spacing, escaping or structure shows."""
    expected = (Path(__file__).parent / "golden" / "paper.md").read_text(encoding="utf-8")
    assert render_latex((TEX_DIR / "paper.tex").read_text(encoding="utf-8")).markdown == expected
