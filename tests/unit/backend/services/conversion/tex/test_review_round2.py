"""Regressions for the review of feature 002 (round 2 of the verification, R2-*).

The finding id is in the test name."""

import time
from pathlib import Path

import pytest
from support.tex_review import doc, md, write

from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.tex.document import convert_document
from clearmd.backend.services.conversion.tex.render import render_latex

BEACON = "https://e.test/b.png"


@pytest.mark.parametrize(
    "body",
    [
        "\\ref{a] [t](javascript:alert(1)) [b}",
        f"\\cite{{<img src={BEACON}>}}",
        f'\\begin{{zz}}<img src="{BEACON}"> ![](https://e.test/c.png)\\end{{zz}}',
        f"\\unknownmacro{{<img src={BEACON}>}}{{![](https://e.test/c.png)}}",
        f"$a <img src={BEACON}> b$",
        f"\\textless img src={BEACON}\\textgreater",
    ],
)
def test_r2_1_2_3_no_output_path_lets_html_or_links_through(body: str) -> None:
    text = md(doc(body))
    assert "<img" not in text and "](javascript" not in text and "](https://e.test" not in text


@pytest.mark.parametrize(
    "body",
    [
        "Antes.\n\n\\# titulo",
        "Antes.\n\n1{}. item",
        "Antes.\n\n-{} item",
        "Titulo\n===\n",
        "Titulo\n-\n",
        "Antes.\n\n***\n",
        "Antes.\n\n\\textasciitilde\\textasciitilde\\textasciitilde\nDespues.",
        "Antes.\n\n[a]: https://e.test/x",
    ],
)
def test_r2_10_document_text_never_becomes_markdown_structure(body: str) -> None:
    text = md(doc(body))
    lines = [line.strip() for line in text.splitlines()]
    assert "===" not in lines and "-" not in lines and "***" not in lines
    assert not any(line.startswith(("# ", "1. ", "- ", "~~~", "[a]:")) for line in lines)


def test_r2_10_clearmd_own_structure_is_kept() -> None:
    text = md(
        doc(
            "\\section{S}\\begin{itemize}\\item a\\end{itemize}\\begin{quote}q\\end{quote}"
            "\\begin{tabular}{c}x\\\\\\end{tabular}\\[ - x \\]\\footnote{n}"
        )
    )
    for expected in ("## S", "- a", "> q", "| x |", "$$\n{}- x\n$$", "[^1]: n"):
        assert expected in text, expected
    assert "\ue000" not in text


def test_r2_10_the_sentinel_cannot_be_forged() -> None:
    assert "\n# x" not in "\n" + md(doc("Antes.\n\n\ue000# x"))


def test_r2_4_unclosed_urls_are_linear(tmp_path: Path) -> None:
    started = time.monotonic()
    convert_document(write(tmp_path, "u.tex", doc("\\url{x " * 30_000)))
    assert time.monotonic() - started < 15


def test_r2_4_many_verb_delimiters_on_one_line_are_linear(tmp_path: Path) -> None:
    line = "".join(f"\\verb{chr(0x21 + n % 30)}" for n in range(40_000))
    started = time.monotonic()
    convert_document(write(tmp_path, "v.tex", doc(line)))
    assert time.monotonic() - started < 15


def test_r2_5_an_iffalse_without_its_fi_hides_nothing_and_is_noted() -> None:
    result = render_latex(doc("Before \\iffalse hidden {\\fi} \\section{Rest} after"))
    assert "## Rest" in result.markdown and "after" in result.markdown
    assert NoteKind.PARSE_RECOVERED in {note.kind for note in result.notes}


def test_r2_6_nested_conditionals_inside_iffalse(tmp_path: Path) -> None:
    write(tmp_path, "old.tex", "OLD CONTENT")
    body = "\\iffalse \\ifx a b\\fi \\input{old} \\fi Visible."
    text = convert_document(write(tmp_path, "main.tex", doc(body))).markdown
    assert "OLD" not in text and "Visible." in text
    listed = md(doc("\\begin{itemize}\\item a\\iffalse\\item hidden\\fi\\item b\\end{itemize}"))
    assert "hidden" not in listed and "- a" in listed and "- b" in listed


def test_r2_7_structural_macros_used_inside_other_macros() -> None:
    preamble = (
        "\\newcommand{\\beq}{\\begin{equation}}\\newcommand{\\eeq}{\\end{equation}}"
        "\\newcommand{\\eqn}[1]{\\beq #1 \\eeq}"
        "\\newcommand{\\bal}{\\begin{align}}\\newcommand{\\eal}{\\end{align}}"
        "\\newcommand{\\myeq}{\\bal}\\newcommand{\\myend}{\\eal}"
    )
    result = render_latex(doc("\\eqn{x=1} y \\myeq a &= b \\myend z", preamble))
    assert "$$\nx=1\n$$" in result.markdown
    assert "\\begin{aligned}\na &= b\n\\end{aligned}" in result.markdown
    assert not [n for n in result.notes if n.kind is NoteKind.UNKNOWN_COMMANDS]


def test_r2_8_renew_order_and_code_the_mask_must_know(tmp_path: Path) -> None:
    preamble = "\\newcommand{\\bx}{\\begin{equation}}\\newcommand{\\ex}{\\end{equation}}"
    text = md(
        doc(
            "\\bx a \\ex \\renewcommand{\\bx}{\\begin{align}}\\renewcommand{\\ex}{\\end{align}}"
            "\\bx b \\ex",
            preamble,
        )
    )
    assert "$$\na\n$$" in text and "\\begin{aligned}\nb\n\\end{aligned}" in text
    write(tmp_path, "secret.tex", "SECRET")
    main = write(
        tmp_path,
        "main.tex",
        doc(
            "\\begin{Verbatim}\n\\input{secret}\\bx\n\\end{Verbatim}"
            "\\lstinline|\\input{secret}| Fin.",
            preamble,
        ),
    )
    converted = convert_document(main).markdown
    assert "SECRET" not in converted and "Fin." in converted
    assert "```\n\\input{secret}\\bx\n```" in converted


def test_r2_9_one_bad_token_never_turns_the_document_into_latex() -> None:
    result = render_latex(doc("Texto bueno. \\begin{itemize}\\item[\\href \\end{itemize} Fin."))
    assert "```latex" not in result.markdown and "Texto bueno." in result.markdown
    # What follows the unclosed "[" is taken by it, as with an unclosed brace: noted.
    assert NoteKind.PARSE_RECOVERED in {note.kind for note in result.notes}


def test_r2_11_one_blank_line_around_code_blocks() -> None:
    text = md(doc("Antes.\\begin{verbatim}\ncode\n\\end{verbatim}Despues."))
    assert "Antes.\n\n```\ncode\n```\n\nDespues." in text


def test_r2_12_parse_errors_keep_their_line_with_structural_macros(tmp_path: Path) -> None:
    source = doc(
        "\\beq x \\eeq\n\nlinea dos\n\n\\textbf{sin cerrar\n",
        "\\newcommand{\\beq}{\\begin{equation}}\\newcommand{\\eeq}{\\end{equation}}\n",
    )
    result = convert_document(write(tmp_path, "e.tex", source))
    (note,) = [n for n in result.notes if n.kind is NoteKind.PARSE_RECOVERED]
    assert note.items[0].subject.startswith("e.tex, line ")


def test_expansions_scale_with_the_document() -> None:
    from clearmd.backend.services.conversion.tex.macros import MacroExpander, expansion_limit

    assert expansion_limit(1024) == 10_000
    assert expansion_limit(1024**2) == 10 * 1024
    assert expansion_limit(2 * 1024**2) == 20 * 1024
    assert MacroExpander({}, 2 * 1024**2).max_expansions == 20 * 1024


def test_s6_a_backslash_before_a_backtick_never_frees_it() -> None:
    from support.markdown_guarantee import broken_promises

    text = md(doc("a \\textbackslash` \\verb|<img src=x>| b"))
    assert broken_promises(text) == []
