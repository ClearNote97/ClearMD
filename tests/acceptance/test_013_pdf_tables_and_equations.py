"""Feature 013 — one test per acceptance criterion (spec/features/013_*/spec.md): hand-made PDFs
through the command line."""

import tomllib
from pathlib import Path

from support.pdf_builder import Box, Text, build_pdf, paragraph

from clearmd.frontend.cli import main

ROOT = Path(__file__).resolve().parents[2]
DATA = [
    ["Year", "Median", "CV", "Maximum"],
    ["2012", "0.871", "0.099", "1.0 (3)"],
    ["2013", "0.861", "0.113", "1.0 (3)"],
    ["2014", "0.863", "0.126", "1.0 (4)"],
]


def converted(workdir: Path, pages: list[list[Text | Box]], *flags: str) -> str:
    docs = workdir / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "paper.pdf").write_bytes(build_pdf(pages))
    assert main([str(docs), "--quiet", *flags]) == 0
    out = workdir / "ClearMD_Output" / "OutputMD" / "docs" / "paper.md"
    return out.read_text(encoding="utf-8")


def grid(rows: list[list[str]], top: float, *, sideways: bool = False) -> list[Text | Box]:
    out: list[Text | Box] = []
    for index, row in enumerate(rows):
        for place, text in zip((0, 130, 230, 330), row, strict=False):
            if sideways:
                out.append(Text(text, 100 + place, 10, x=120 + 16 * index, sideways=True))
            else:
                out.append(Text(text, top - 16 * index, 10, x=72 + place))
    return out


def test_ac_01_an_aligned_table_and_not_prose(workdir: Path) -> None:
    prose = paragraph(
        ["Some words    with gaps     in a line", "and more     words here    and there"], top=500
    )
    markdown = converted(workdir, [[*grid(DATA, 700), *prose]])
    assert "| Year | Median | CV | Maximum |\n|---|---|---|---|" in markdown
    assert "| 2014 | 0.863 | 0.126 | 1.0 (4) |" in markdown
    assert "Some words" in markdown and "| Some" not in markdown


def test_ac_02_a_ruled_table_keeps_a_wrapped_cell_whole(workdir: Path) -> None:
    rules: list[Text | Box] = [Box(70, y, 260, 0.5) for y in (705, 685, 650)]
    rules += [Box(x, 650, 0.5, 55) for x in (70, 200, 330)]
    texts: list[Text | Box] = [
        Text("Name", 690, 9, x=75), Text("Role", 690, 9, x=205),
        Text("Ana", 670, 9, x=75), Text("Judge", 670, 9, x=205), Text("of peace", 658, 9, x=205),
    ]  # fmt: skip
    markdown = converted(workdir, [rules + texts])
    assert "| Name | Role |\n|---|---|\n| Ana | Judge of peace |" in markdown


def test_ac_03_a_sideways_table_is_read_upright_without_the_header(workdir: Path) -> None:
    body = paragraph(["The article's text on every page, long enough to be its body."], top=700)
    pages: list[list[Text | Box]] = [
        [Text(f"{n} | Journal of Courts", 760, 8), *body] for n in range(1, 6)
    ]
    pages[2] = [Text("3 | Journal of Courts", 760, 8), *grid(DATA, 0, sideways=True)]
    markdown = converted(workdir, pages)
    assert "| Year | Median | CV | Maximum |" in markdown
    assert "| 2013 | 0.861 | 0.113 | 1.0 (3) |" in markdown
    assert "Journal of Courts" not in markdown


def equation_page() -> list[Text | Box]:
    return [
        *paragraph(["The program is stated as follows, for every court:"], top=700),
        Text("EF = max t", 670, 11, x=200),
        Text("s.t. z <= 1", 652, 11, x=200),
        Text("(5)", 661, 11, x=520),
        *paragraph(["where the variables are the ones defined in the text above it."], top=620),
    ]


def test_ac_04_an_equation_whole_as_text_or_as_a_picture(workdir: Path) -> None:
    markdown = converted(workdir, [equation_page()])
    block = markdown.split("```")[1]
    assert "EF = max t" in block and "s.t. z <= 1" in block and "(5)" in block
    pictured = converted(workdir, [equation_page()], "--images", "--overwrite")
    assert "![](paper_images/image-001.png)" in pictured and "```" not in pictured
    out = workdir / "ClearMD_Output" / "OutputMD" / "docs" / "paper_images" / "image-001.png"
    assert out.read_bytes().startswith(b"\x89PNG")


def test_ac_05_captions_and_a_table_of_contents(workdir: Path) -> None:
    entries = [
        "Dedicatoria ............................................. ii",
        "3.1 Tipo y diseño de investigación ....................... 14",
    ]
    contents = paragraph(["Índice", *entries], top=300)
    caption = [Text("Table 1: Medians by year.", 730, 10)]
    markdown = converted(workdir, [[*caption, *grid(DATA, 710), *contents]])
    assert "Table 1: Medians by year.\n\n| Year |" in markdown
    assert f"Índice\n\n{entries[0]}\n\n{entries[1]}" in markdown


def test_ac_06_camelot_is_credited_and_not_a_dependency() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert not any("camelot" in item.lower() for item in project["project"]["dependencies"])
    for readme in ("README.md", "README.es.md"):
        assert "Camelot" in (ROOT / readme).read_text(encoding="utf-8")
