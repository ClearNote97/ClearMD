"""Regressions for the review of feature 002 (code review H*/M*/L*, security audit F*).

Each test reproduces the reported input first; the finding id is in the test name.
"""

import time
from pathlib import Path

import pytest

from clearmd.backend.schemas.notes import NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.tex.document import convert_document
from clearmd.backend.services.conversion.tex.render import render_latex


def md(latex: str) -> str:
    return render_latex(latex).markdown


def doc(body: str, preamble: str = "") -> str:
    return f"\\documentclass{{article}}{preamble}\\begin{{document}}{body}\\end{{document}}"


def kinds(latex: str) -> set[NoteKind]:
    return {note.kind for note in render_latex(latex).notes}


def write(folder: Path, name: str, text: str | bytes) -> Path:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")
    return path


# --- Robustness: a file never fails as a whole (AC-21) -------------------------------------------


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


def test_m5_def_with_names_pylatexenc_knows_and_with_parameters() -> None:
    result = render_latex(doc("\\def\\b{BB}\\def\\d{DD} \\b{} \\d{}"))
    assert "BB DD" in result.markdown
    assert NoteKind.PARSE_RECOVERED not in {note.kind for note in result.notes}
    parametrized = render_latex(doc("\\def\\foo#1{[#1]} rest"))
    assert "#1[#1] rest" not in parametrized.markdown
    (unknown,) = [n for n in parametrized.notes if n.kind is NoteKind.UNKNOWN_COMMANDS]
    assert NoteItem("\\def") in unknown.items


def test_m2_definitions_follow_the_document_order_across_includes(tmp_path: Path) -> None:
    write(tmp_path, "defs.tex", "\\newcommand{\\x}{DEFS}")
    main = write(
        tmp_path,
        "main.tex",
        doc("\\x", "\\newcommand{\\x}{MAIN}\\input{defs}\\renewcommand{\\x}{RENEW}"),
    )
    assert "RENEW" in convert_document(main).markdown


def test_m3_an_include_written_inside_verbatim_is_never_followed(tmp_path: Path) -> None:
    write(tmp_path, "defs.tex", "\\newcommand{\\x}{DEFS}")
    main = write(
        tmp_path, "main.tex", doc("\\begin{verbatim}\n\\input{defs}\n\\end{verbatim}\n\\x{}")
    )
    result = convert_document(main)
    assert "DEFS" not in result.markdown and "\\input{defs}" in result.markdown


def test_l1_babel_main_language_is_the_last_option() -> None:
    abstract = "\\begin{abstract}T\\end{abstract}"
    assert "## Abstract" in md(doc(abstract, "\\usepackage[spanish,english]{babel}"))
    assert "## Abstract" in md(doc(abstract, "%\\usepackage[spanish]{babel}\n"))
    assert "## Resumen" in md(doc(abstract, "\\usepackage[english,spanish]{babel}"))


def test_l2_argument_values_are_never_substituted_again() -> None:
    assert "$A-#1$" in md(doc("$\\x{A}{#1}$", "\\newcommand{\\x}[2]{#1-#2}"))
    assert "$#a a$" not in md(doc("$\\y{a}$", "\\newcommand{\\y}[1]{##1 #1}"))


def test_l3_empty_bold_and_code_with_backticks() -> None:
    assert "****" not in md(doc("a \\textbf{} b"))
    assert "`` a`b ``" in md(doc("\\texttt{a`b}"))


def test_l4_declared_latin1_with_windows_quotes(tmp_path: Path) -> None:
    source = b"\\usepackage[latin1]{inputenc}\\begin{document}\x93cita\x94 a\xf1o\\end{document}"
    text = convert_document(write(tmp_path, "w.tex", source)).markdown
    assert "“cita” año" in text


def test_l10_text_before_the_first_item_and_cite_prenotes() -> None:
    assert "antes" in md(doc("\\begin{itemize} antes \\item a\\end{itemize}"))
    assert "[see @a, p. 3]" in md(doc("\\citep[see][p. 3]{a}"))


# --- Budgets and output safety (security audit) -----------------------------------------------


def test_f1_l2_arguments_are_not_substituted_again_so_the_reported_bomb_is_inert(
    tmp_path: Path,
) -> None:
    source = (
        "\\newcommand\\x[3]{" + "#3" * 200 + "}\n"
        "$\\x{" + "a" * 1000 + "}{" + "#1" * 200 + "}{" + "#2" * 200 + "}$\n"
    )
    result = convert_document(write(tmp_path, "m.tex", source))
    assert len(result.markdown) < 2 * 1024**2  # 200 copies of "#2"*200, as TeX would write
    assert "#2#2" in result.markdown and "a" * 1000 not in result.markdown


def test_f1_an_expansion_past_the_budget_is_refused_before_it_is_built(tmp_path: Path) -> None:
    source = "\\newcommand\\w[1]{" + "#1" * 1000 + "}\n$\\w{" + "a" * 100_000 + "}$\n"
    started = time.monotonic()
    result = convert_document(write(tmp_path, "w.tex", source))  # 100 MB if it were built
    assert time.monotonic() - started < 10
    limits = [i for n in result.notes if n.kind is NoteKind.MACRO_LIMIT_REACHED for i in n.items]
    assert limits == [NoteItem("\\w", NoteReason.GROWTH.value)]
    assert len(result.markdown) < 4 * 1024**2


def test_f4_every_file_is_read_once_on_one_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from clearmd.backend.services.conversion.tex import includes

    read: list[str] = []
    real = includes.read_inside

    def counting(folder: Path, relative: object, max_bytes: int) -> bytes:
        read.append(str(relative))
        return real(folder, relative, max_bytes)  # type: ignore[arg-type]

    monkeypatch.setattr(includes, "read_inside", counting)
    write(tmp_path, "a.tex", "\\newcommand{\\y}{Y}")
    main = write(tmp_path, "main.tex", doc("\\y", "\\input{a}"))
    assert "Y" in convert_document(main).markdown
    assert read == ["a.tex"]


@pytest.mark.parametrize(
    "argument", ["http://evil/t.png", "//host/share/x.png", "/etc/x.png", "../out.png"]
)
def test_f7_images_outside_the_folder_are_never_links(argument: str, tmp_path: Path) -> None:
    text = convert_document(
        write(tmp_path, "g.tex", doc(f"\\includegraphics{{{argument}}}"))
    ).markdown
    assert "](" not in text and argument in text


def test_f7_only_image_files_are_looked_up(tmp_path: Path) -> None:
    write(tmp_path, ".ssh/id_rsa", "secret")
    text = convert_document(write(tmp_path, "g.tex", doc("\\includegraphics{.ssh/id_rsa}")))
    assert "../" not in text.markdown


def test_f7_link_targets_are_escaped(tmp_path: Path) -> None:
    write(tmp_path, "img/a (1).png", b"png")
    text = convert_document(
        write(tmp_path, "g.tex", doc("\\includegraphics{img/a (1)}")), tmp_path / "out.md"
    ).markdown
    assert "![](<img/a (1).png>)" in text


def test_f8_a_kept_table_with_backticks_stays_one_block_and_scripts_are_not_links() -> None:
    text = md(doc("\\begin{tabular}{cc}\\multicolumn{2}{c}{```}\\\\\\end{tabular}"))
    assert "````latex" in text
    script = md(doc("\\href{javascript:alert(1)}{t}"))
    assert "](javascript:" not in script and "t" in script


def test_f9_note_subjects_have_a_bounded_length() -> None:
    name = "\\" + "a" * 5000
    (note,) = [n for n in render_latex(doc(name)).notes if n.kind is NoteKind.UNKNOWN_COMMANDS]
    assert len(note.items[0].subject) <= 201


# --- Adversarial verification of the fixes (N*, I*, partial F*/H*) -------------------------------


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
    assert "](" not in md(doc("\\href{javascript&#58;alert(1)}{click}"))
    injected = md(doc("\\href{https://e.test}{a](javascript:alert(1)) [b}"))
    assert "](javascript" not in injected
    alt = md(
        doc(
            "\\begin{figure}\\includegraphics{a}"
            "\\caption{x](https://e.test/b.png) ![y}\\end{figure}"
        )
    )
    assert "](https://e.test" not in alt
    plain = md(doc('Look ![](https://e.test/beacon.png) and <img src="https://e.test/b.png">'))
    assert "](https" not in plain and "<img" not in plain


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
    assert time.monotonic() - started < 20


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
