"""Feature 015 — one test per acceptance criterion (spec/features/015_*/spec.md): hand-made PDFs
through the command line."""

import tomllib
from pathlib import Path

from support.pdf_builder import Box, Text, build_pdf, paragraph

from clearmd.backend.services.conversion.pdf.latex import MAX_ROWS
from clearmd.frontend.cli import main

ROOT = Path(__file__).resolve().parents[2]
BEFORE = "The change is then measured as follows, for each firm and period:"
AFTER = "where the variables are the ones defined in the text above it."


def converted(workdir: Path, pages: list[list[Text | Box]], *flags: str) -> str:
    docs = workdir / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "paper.pdf").write_bytes(build_pdf(pages))
    assert main([str(docs), "--quiet", "--overwrite", *flags]) == 0
    out = workdir / "ClearMD_Output" / "OutputMD" / "docs" / "paper.md"
    return out.read_text(encoding="utf-8")


def fraction_page(*, number: str = "") -> list[Text | Box]:
    """ "C = (a + b) / c", the fraction drawn as a bar, in the page's reading order."""
    label = [Text(number, 652, 11, x=520)] if number else []
    return [
        *paragraph([BEFORE], top=700),
        Text("a + b", 660, 11, x=225),
        Box(224, 657, 30, 0.6),
        Text("C =", 652, 11, x=200),
        *label,
        Text("c", 646, 11, x=236),
        *paragraph([AFTER], top=610),
    ]


def test_ac_01_a_fraction_is_written_as_latex(workdir: Path) -> None:
    markdown = converted(workdir, [fraction_page(number="(7)")])
    assert f"{BEFORE}\n\n$$\nC = \\frac{{a + b}}{{c}} \\tag{{7}}\n$$\n\n{AFTER}" in markdown


def test_ac_02_an_equation_with_no_number_is_found_by_its_bar(workdir: Path) -> None:
    markdown = converted(workdir, [fraction_page()])
    assert "$$\nC = \\frac{a + b}{c}\n$$" in markdown
    assert BEFORE in markdown and AFTER in markdown


def test_ac_03_scripts_brackets_and_rows(workdir: Path) -> None:
    page: list[Text | Box] = [
        *paragraph([BEFORE], top=700),
        Text("EF", 670, 11, x=200),
        Text("t", 674, 7, x=214.1),
        Text("o", 667, 7, x=214.1),
        Text("= max z", 670, 11, x=222),
        Text("s.t. z <= 1", 652, 11, x=200),
        Text("(5)", 661, 11, x=520),
        *paragraph([AFTER], top=620),
    ]
    markdown = converted(workdir, [page])
    rows = r"\displaystyle EF_{o}^{t} = \max z \\ \displaystyle s.t. z <= 1"
    latex = rf"\begin{{array}}{{l}} {rows} \end{{array}} \tag{{5}}"
    assert f"$$\n{latex}\n$$" in markdown


def test_ac_04_with_the_images_folder_latex_too(workdir: Path) -> None:
    markdown = converted(workdir, [fraction_page(number="(7)")], "--images")
    assert "\\frac{a + b}{c} \\tag{7}" in markdown and "![](" not in markdown


def test_ac_05_an_equation_not_understood_is_written_as_before(workdir: Path) -> None:
    rows = [Text(f"x{n} = {n}", 690 - 14 * n, 11, x=200) for n in range(MAX_ROWS + 1)]
    page: list[Text | Box] = [*rows[:7], Text("(9)", 690 - 14 * 6, 11, x=520), *rows[7:]]
    markdown = converted(workdir, [page])
    assert "$$" not in markdown and "```\nx0 = 0" in markdown
    pictured = converted(workdir, [page], "--images")
    assert "![](paper_images/image-001.png)" in pictured


def test_ac_06_a_ruled_table_or_a_rule_in_prose_is_no_equation(workdir: Path) -> None:
    table: list[Text | Box] = [
        Text("N", 700, 10, x=100), Box(95, 696, 30, 0.6), Text("45", 686, 10, x=100),
        Box(95, 682, 30, 0.6), Text("12", 672, 10, x=100),
    ]  # fmt: skip
    prose: list[Text | Box] = [
        *paragraph([BEFORE], top=600),
        Box(72, 594, 40, 0.6),
        *paragraph([AFTER], top=586),
    ]
    markdown = converted(workdir, [[*table, *prose]])
    assert "$$" not in markdown and BEFORE in markdown and AFTER in markdown


def test_ac_07_documented() -> None:
    adr = ROOT / "docs" / "decisions" / "0036-equations-as-latex.md"
    assert adr.exists() and "Status:** accepted" in adr.read_text(encoding="utf-8")
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert tuple(map(int, version["project"]["version"].split("."))) >= (0, 10, 0)
