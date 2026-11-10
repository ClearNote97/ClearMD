"""Regressions for the review of feature 002 (never-fail guards and linear time).

The finding id is in the test name."""

import sys
import time
from pathlib import Path

import pytest
from support.markdown_guarantee import live_syntax
from support.tex_review import doc, md, write

from clearmd.backend.schemas.notes import NoteKind
from clearmd.backend.services.conversion.tex.document import convert_document
from clearmd.backend.services.conversion.tex.render import render_latex


def test_n1_a_macro_that_opens_an_environment_keeps_the_document() -> None:
    preamble = "\\newcommand{\\beq}{\\begin{equation}}\\newcommand{\\eeq}{\\end{equation}}"
    text = md(doc("Intro text.\\beq x=1 \\eeq\\section{More}Last.", preamble))
    assert "Intro text." in text and "## More" in text and "Last." in text
    assert "$$\nx=1\n$$" in text
    listed = md(
        doc(
            "\\bi\\item a\\item b\\ei Fin.",
            "\\newcommand{\\bi}{\\begin{itemize}}\\newcommand{\\ei}{\\end{itemize}}",
        )
    )
    assert "- a\n- b" in listed and "Fin." in listed


def test_n2_a_strange_argument_count_never_fails_the_file() -> None:
    result = render_latex(doc("\\x y", "\\newcommand{\\x}[²]{a}"))
    assert "y" in result.markdown


def test_n2_any_converter_failure_keeps_the_file_as_latex(monkeypatch: pytest.MonkeyPatch) -> None:
    from clearmd.backend.services.conversion.tex import render

    def broken(*args: object, **kwargs: object) -> None:
        raise KeyError("boom")

    monkeypatch.setattr(render, "top_level", broken)
    result = render_latex(doc("Texto."))
    assert "```latex" in result.markdown and "Texto." in result.markdown
    assert NoteKind.PARSE_RECOVERED in {note.kind for note in result.notes}


def test_n3_unclosed_fence_openers_are_linear(tmp_path: Path) -> None:
    openers = "".join("`" * (1000 + n) + "\n" for n in range(10))
    source = doc(f"\\begin{{zz}}\n{openers}\\end{{zz}}\n" + "texto llano. " * 16_000)
    started = time.monotonic()
    convert_document(write(tmp_path, "f.tex", source))
    assert time.monotonic() - started < 8


def test_n4_chapters_written_by_a_macro_keep_sections_below_them() -> None:
    text = md(doc("\\mychap{C}\\section{S}", "\\newcommand{\\mychap}[1]{\\chapter{#1}}"))
    assert "## C" in text and "### S" in text


@pytest.mark.parametrize(
    "line",
    [
        "line\\\\% old: \\input{secret}\n",
        "\\iffalse\n\\input{secret}\n\\fi\n",
        "\\begin{comment}\n\\input{secret}\nhidden text\n\\end{comment}\n",
    ],
)
def test_i1_i3_i4_commented_includes_are_never_followed(line: str, tmp_path: Path) -> None:
    write(tmp_path, "secret.tex", "SECRET FIRST LINE\nSECRET SECOND")
    text = convert_document(write(tmp_path, "main.tex", doc(line + "Visible."))).markdown
    assert "SECRET" not in text and "hidden" not in text and "Visible." in text


def test_i6_i7_an_include_left_in_the_text_is_always_noted(tmp_path: Path) -> None:
    write(tmp_path, "ch.tex", "CAPITULO")
    result = convert_document(
        write(tmp_path, "main.tex", doc("\\url{a%20b} \\input{ch} after \\input{{ch}}"))
    )
    assert "CAPITULO" in result.markdown
    refused = [i for n in result.notes if n.kind is NoteKind.INCLUDE_NOT_FOLLOWED for i in n.items]
    assert [item.subject for item in refused] == ["{ch}"]


@pytest.mark.parametrize(
    "argument", ["https&#58;//evil.test/a.png", "https&colon;//e.test/a.png", "&#47;&#47;e/a.png"]
)
def test_f7_entities_never_make_a_remote_image(argument: str, tmp_path: Path) -> None:
    text = convert_document(write(tmp_path, "g.tex", doc(f"\\includegraphics{{{argument}}}")))
    assert "](" not in text.markdown


def test_f8_entities_and_text_never_make_links_or_html() -> None:
    assert not live_syntax(md(doc("\\href{javascript&#58;alert(1)}{click}")))
    injected = md(doc("\\href{https://e.test}{a](javascript:alert(1)) [b}"))
    assert not live_syntax(injected)
    alt = md(
        doc(
            "\\begin{figure}\\includegraphics{a}"
            "\\caption{x](https://e.test/b.png) ![y}\\end{figure}"
        )
    )
    # The figure's own picture (a) stays; its caption never makes another.
    assert live_syntax(alt) == ["image: 'a'"]
    plain = md(doc('Look ![](https://e.test/beacon.png) and <img src="https://e.test/b.png">'))
    assert not live_syntax(plain)


def test_l3_text_never_starts_a_block_by_accident() -> None:
    text = md(doc("Primera.\n\n# no es un titulo\n\n> ni una cita"))
    assert "\n# no" not in text and "\n> ni" not in text
    assert "no es un titulo" in text


def test_n5_code_text_is_left_as_written() -> None:
    assert "``` a[0] ``x'' ```" in md(doc("\\texttt{a[0] ``x''}"))


def test_f3_image_lookups_are_bounded(tmp_path: Path) -> None:
    images = "".join(f"\\includegraphics{{n{n}}}" for n in range(3000))
    started = time.monotonic()
    convert_document(write(tmp_path, "i.tex", doc(images, "\\graphicspath{" + "{a/}" * 64 + "}")))
    assert time.monotonic() - started < (60 if sys.platform == "win32" else 20)  # slower stat


def test_f9_the_list_of_refused_includes_is_bounded(tmp_path: Path) -> None:
    body = "".join(f"\\input{{m{n}}}" for n in range(3000))
    result = convert_document(write(tmp_path, "r.tex", doc(body)))
    refused = [n for n in result.notes if n.kind is NoteKind.INCLUDE_NOT_FOLLOWED]
    assert len(refused[0].items) <= 1000


def test_h7_indentation_after_a_block_on_the_same_line() -> None:
    text = md(
        doc("\\section{A}    Texto tras titulo.\\begin{itemize}\\item a\\end{itemize}    cola")
    )
    assert "\n    " not in text
    assert "Texto tras titulo." in text and "cola" in text


def test_n5_small_gaps() -> None:
    # TeX: the comment hides "}" and the end of line; the space after "\\x" is eaten.
    assert "a btail" in md(doc("\\x tail", "\\def\\x{a % }\n b}"))
    # \makeatletter internals are not expanded (ADR-0022): the definition never leaks.
    internal = md(doc("\\makeatletter\\def\\@foo{F}\\makeatother\\@foo"))
    assert "\\def" not in internal and "{F}" not in internal
    abstract = "\\begin{abstract}T\\end{abstract}"
    assert "## Abstract" in md(doc(abstract, "\\usepackage[main=english,spanish]{babel}"))
    assert "## Resumen" in md(doc(abstract, "\\setdefaultlanguage{spanish}"))


def test_n5_a_macro_parameter_in_an_include_is_not_an_include(tmp_path: Path) -> None:
    result = convert_document(
        write(tmp_path, "m.tex", doc("x", "\\newcommand{\\inc}[1]{\\input{#1}}"))
    )
    assert NoteKind.INCLUDE_NOT_FOLLOWED not in {note.kind for note in result.notes}


# --- Round 2 of the verification (R2-*) ---------------------------------------------------
