"""The author's macros, expanded with limits (ADR-0022, AC-16, AC-17)."""

import shutil
import time
from pathlib import Path

import pytest
from support import TEX_DIR

from clearmd.backend.schemas.notes import NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.tex.document import convert_document
from clearmd.backend.services.conversion.tex.render import render_latex


def md(latex: str) -> str:
    return render_latex(latex).markdown


@pytest.mark.parametrize(
    ("definitions", "body", "expected"),
    [
        ("\\newcommand{\\R}{\\mathbb{R}}", "$x \\in \\R$", "$x \\in \\mathbb{R}$"),
        (
            "\\newcommand{\\norm}[1]{\\left\\lVert #1 \\right\\rVert}",
            "$\\norm{x+y}$",
            "$\\left\\lVert x+y \\right\\rVert$",
        ),
        ("\\newcommand{\\pair}[2][0]{(#1, #2)}", "$\\pair{a}$ $\\pair[b]{c}$", "$(0, a)$ $(b, c)$"),
        (
            "\\DeclareMathOperator{\\argmax}{arg\\,max}",
            "$\\argmax_x$",
            "$\\operatorname{arg\\,max}_x$",
        ),
        ("\\DeclareMathOperator*{\\lim}{lim}", "$\\lim_x$", "$\\operatorname*{lim}_x$"),
        ("\\newcommand{\\R}{\\mathbb{R}}\\newcommand{\\Rn}{\\R^n}", "$\\Rn$", "$\\mathbb{R}^n$"),
        ("\\newcommand{\\R}{\\mathbb{R}}", "$\\frac{1}{\\R}$", "$\\frac{1}{\\mathbb{R}}$"),
    ],
)
def test_macros_expand_in_math(definitions: str, body: str, expected: str) -> None:
    assert expected in md(definitions + body)


def test_macros_expand_in_text_through_the_normal_rules() -> None:
    text = md(
        "\\def\\ClearMD{ClearMD}\\newcommand{\\destacar}[1]{\\textbf{#1}}"
        "\\ClearMD{} y \\destacar{esto}"
    )
    assert "ClearMD y **esto**" in text
    assert "def" not in text


def test_renew_replaces_and_provide_keeps_the_first() -> None:
    text = md(
        "\\newcommand{\\a}{uno}\\renewcommand{\\a}{dos}\\providecommand{\\a}{tres}"
        "\\providecommand{\\b}{cuatro}\\a{} \\b{}"
    )
    assert "dos cuatro" in text


def test_definitions_from_an_included_file_apply(tmp_path: Path) -> None:
    shutil.copytree(TEX_DIR / "thesis", tmp_path / "thesis")
    text = convert_document(tmp_path / "thesis" / "main.tex").markdown
    assert "$x \\in \\mathbb{R}$" in text
    assert "\\left\\lVert x \\right\\rVert" in text
    assert "$(0, a)$, $(b, c)$" in text
    assert "\\operatorname{arg\\,max}_{\\theta}" in text
    assert "Herramienta: ClearMD." in text


def test_a_defined_macro_is_never_reported_as_unknown() -> None:
    result = render_latex("\\newcommand{\\miMacro}{x}\\miMacro")
    assert not [n for n in result.notes if n.kind is NoteKind.UNKNOWN_COMMANDS]


def _limit_notes(path: Path) -> list[NoteItem]:
    result = convert_document(path)
    return [i for n in result.notes if n.kind is NoteKind.MACRO_LIMIT_REACHED for i in n.items]


def test_a_recursive_macro_stops_at_the_nesting_limit_quickly() -> None:
    started = time.monotonic()
    result = convert_document(TEX_DIR / "hostile" / "recursive_macro.tex")
    assert time.monotonic() - started < 5
    assert "$\\loop$" in result.markdown  # left as written
    limits = [i for n in result.notes if n.kind is NoteKind.MACRO_LIMIT_REACHED for i in n.items]
    assert limits == [NoteItem("\\loop", NoteReason.NESTING.value)]


def test_an_exponential_macro_stops_at_the_expansion_limit_quickly() -> None:
    started = time.monotonic()
    result = convert_document(TEX_DIR / "hostile" / "exponential_macro.tex")
    assert time.monotonic() - started < 10
    assert len(result.markdown) < 2 * 1024**2
    assert "$\\bombaa$" in result.markdown
    limits = [i for n in result.notes if n.kind is NoteKind.MACRO_LIMIT_REACHED for i in n.items]
    assert limits == [NoteItem("\\bombaa", NoteReason.EXPANSIONS.value)]


def test_growth_is_limited(tmp_path: Path) -> None:
    # Each expansion adds 100 KB: the text would outgrow 4x the source + 1 MiB long before
    # 10,000 expansions or 64 levels.
    big = "x" * 100_000
    body = "".join("\\big" for _ in range(30))
    path = tmp_path / "growth.tex"
    path.write_text(f"\\newcommand{{\\big}}{{{big}}}{body}", encoding="utf-8")
    limits = _limit_notes(path)
    assert limits == [NoteItem("\\big", NoteReason.GROWTH.value)]
