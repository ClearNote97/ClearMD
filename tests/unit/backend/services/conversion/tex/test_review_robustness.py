"""Regressions for the review of feature 002 (robustness, headings, figures).

The finding id is in the test name."""

import time
from pathlib import Path

import pytest
from support.tex_review import doc, md, write

from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.tex.document import convert_document
from clearmd.backend.services.conversion.tex.render import render_latex


@pytest.mark.parametrize("latex", ["\\verb*|a b| y", "\\verb x y", "x \\verb"])
def test_h1_odd_verb_never_fails_the_file(latex: str) -> None:
    result = render_latex(doc(latex))
    assert "y" in result.markdown or latex.endswith("verb")


def test_h1_starred_verb_keeps_its_text() -> None:
    assert "`a b`" in md(doc("\\verb*|a b|"))


@pytest.mark.parametrize(
    "latex",
    [
        "{" * 400 + "x" + "}" * 400,
        "\\begin{itemize}\\item " * 500 + "x" + "\\end{itemize}" * 500,
        "\\input{" * 20_000,
    ],
    ids=["braces", "lists", "inputs"],  # short ids: pytest puts the id in an environment variable
)
def test_m4_f2_deep_nesting_converts_with_a_note(latex: str, tmp_path: Path) -> None:
    started = time.monotonic()
    result = convert_document(write(tmp_path, "deep.tex", latex))
    assert time.monotonic() - started < 30
    assert result.markdown.strip()
    assert NoteKind.PARSE_RECOVERED in {note.kind for note in result.notes}


def test_m6_an_unclosed_code_block_keeps_the_rest_of_the_text() -> None:
    text = md("\\begin{lstlisting}\ncode\n\\section{After} text")
    assert "code" in text and "\\section{After} text" in text


def test_f6_a_nul_in_an_include_is_a_refusal_not_a_failure(tmp_path: Path) -> None:
    result = convert_document(write(tmp_path, "n.tex", b"\\input{a\x00b}\nhola\n"))
    assert "hola" in result.markdown
    assert NoteKind.INCLUDE_NOT_FOLLOWED in {note.kind for note in result.notes}


# --- Faithful rendering of the subset ---------------------------------------------------------


def test_h2_a_comment_inside_math_never_swallows_the_next_row() -> None:
    text = md(doc("\\begin{align}\na &= b \\\\ % first\nc &= d\n\\end{align} $a % c\n + b$"))
    assert "%" not in text
    assert "a &= b \\\\ c &= d" in text and "$a + b$" in text


def test_h3_commented_or_verbatim_sectioning_does_not_shift_headings() -> None:
    text = md(
        doc(
            "% \\part{old}\n\\begin{verbatim}\n\\chapter{x}\n\\end{verbatim}"
            "\\section{A}\\subsection{B}"
        )
    )
    assert "\n## A\n" in f"\n{text}" and "\n### B\n" in text


@pytest.mark.parametrize(
    ("latex", "expected"),
    [("\\part{P}\\chapter{C}", ["## P", "### C"]), ("\\section{S}\\paragraph{P} t", ["## S"])],
)
def test_h4_part_and_paragraph_have_their_title(latex: str, expected: list[str]) -> None:
    text = md(doc(latex))
    for heading in expected:
        assert heading in text
    assert "##\n" not in text and "P" in text


def test_h5_an_image_outside_a_figure_is_an_image() -> None:
    text = md(doc("See \\includegraphics[width=3cm]{a.png} here"))
    assert "![](a.png)" in text and "g r a p h i c s" not in text


@pytest.mark.parametrize(
    "latex",
    [
        "A\\index{word}L",
        "A\\addcontentsline{toc}{chapter}{Intro}L",
        "A\\pagestyle{empty}\\thispagestyle{plain}L",
        "A\\bibliographystyle{plain}\\nocite{x}L",
        "A\\addbibresource{refs.bib}L",
    ],
)
def test_h6_dropped_commands_take_their_arguments_with_them(latex: str) -> None:
    assert md(doc(latex)).strip() == "AL"


def test_h6_thanks_and_cline_leave_nothing_behind() -> None:
    text = md(doc("\\maketitle", "\\title{T \\thanks{t}}"))
    assert text.startswith("# T\n") or text.strip() == "# T"
    table = md(doc("\\begin{tabular}{c}\\cline{1-1} a\\\\\\cmidrule(lr){1-1} b\\\\\\end{tabular}"))
    assert "1-1" not in table and "(lr)" not in table and "| a |" in table


def test_h7_source_indentation_never_becomes_a_code_block() -> None:
    text = md(doc("Para one.\n\n    Indented para text.\n"))
    assert "\nIndented para text." in text


def test_h8_m11_a_figure_keeps_its_other_content_and_each_caption() -> None:
    text = md(
        doc(
            "\\begin{figure}\\begin{tabular}{c}a\\\\\\end{tabular}"
            "\\begin{subfigure}{.5\\textwidth}\\includegraphics{x}\\caption{A}\\end{subfigure}"
            "\\begin{subfigure}{.5\\textwidth}\\includegraphics{y}\\caption{B}\\end{subfigure}"
            "\\caption{Both}\\end{figure}"
        )
    )
    assert "| a |" in text
    assert "![A](x)" in text and "![B](y)" in text
    assert "*Both*" in text


def test_f3_a_caption_is_written_once_for_many_images() -> None:
    images = "\\includegraphics{a}" * 50
    text = md(doc(f"\\begin{{figure}}{images}\\caption{{{'c' * 1000}}}\\end{{figure}}"))
    assert text.count("c" * 1000) == 1


def test_m7_a_percent_in_a_url_is_part_of_the_url() -> None:
    text = md(doc("\\url{https://x.com/a%20c} y \\href{https://e.org/%20}{t} after"))
    assert "<https://x.com/a%20c>" in text
    assert "[t](https://e.org/%20) after" in text


def test_m8_a_title_set_in_the_body_or_an_include_is_kept(tmp_path: Path) -> None:
    assert md(doc("\\title{T}\\maketitle")).startswith("# T")
    write(tmp_path, "titlepage.tex", "\\title{Desde include}")
    main = write(tmp_path, "main.tex", doc("\\maketitle Texto.", "\\input{titlepage}"))
    assert convert_document(main).markdown.startswith("# Desde include")


def test_m9_captions_of_tables_wherever_they_are_and_longtable() -> None:
    text = md(
        doc(
            "\\begin{table}\\begin{center}\\caption{Cap}"
            "\\begin{tabular}{c}a\\\\\\end{tabular}\\end{center}\\end{table}"
            "\\begin{longtable}{cc}\\caption{L}\\\\ a & b \\\\ \\endhead c & d \\\\\\end{longtable}"
        )
    )
    assert "*Cap*" in text and "*L*" in text
    assert "| a | b |\n|---|---|\n| c | d |" in text
    assert "\\caption" not in text and "endhead" not in text and "cc" not in text


def test_m10_code_blocks_keep_their_blank_lines_also_in_lists() -> None:
    text = md(doc("\\begin{verbatim}\na  \n\n\n\nb\n\\end{verbatim}"))
    assert "a  \n\n\n\nb" in text
    listed = md(
        doc("\\begin{itemize}\\item x\\begin{verbatim}\na\n\nb\n\\end{verbatim}\\end{itemize}")
    )
    assert "a\n\n  b" in listed or "a\n\nb" in listed
