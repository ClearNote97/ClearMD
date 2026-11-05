"""Regressions for the review of feature 002 (macros, includes and encodings).

The finding id is in the test name."""

import time
from pathlib import Path

import pytest
from support.tex_review import doc, md, write

from clearmd.backend.schemas.notes import NoteItem, NoteKind, NoteReason
from clearmd.backend.services.conversion.tex.document import convert_document
from clearmd.backend.services.conversion.tex.render import render_latex


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
