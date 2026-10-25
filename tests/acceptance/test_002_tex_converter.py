"""Feature 002 — one test per acceptance criterion (spec/features/002_*/spec.md)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from support import TEX_DIR

from clearmd.frontend.cli import main


def copy_tex(workdir: Path, *names: str) -> list[Path]:
    copies = []
    for name in names:
        source = TEX_DIR / name
        target = workdir / name
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        copies.append(target)
    return copies


def output(workdir: Path, name: str) -> str:
    return (workdir / "ClearMD_Output" / "OutputMD" / name).read_text(encoding="utf-8")


def summary(workdir: Path) -> str:
    return (workdir / "ClearMD_Output" / "Resumen_ClearMD.md").read_text(encoding="utf-8")


def test_ac_01_a_tex_file_converts_through_the_pipeline(workdir: Path) -> None:
    (paper,) = copy_tex(workdir, "paper.tex")
    copy_tex(workdir, "img")
    assert main([str(paper), "--quiet"]) == 0
    assert "fixture-tex-paper" in output(workdir, "paper.md")
    assert "| `paper.tex` | `OutputMD/paper.md` | TEX |" in summary(workdir)


def test_ac_02_latex_without_extension_is_detected_by_content(workdir: Path) -> None:
    (source,) = copy_tex(workdir, "no_extension_latex")
    assert main([str(source), "--quiet"]) == 0
    assert "fixture-tex-paper" in output(workdir, "no_extension_latex.md")
    assert "TEX, detected by content" in summary(workdir)


def test_ac_03_the_cli_process_never_imports_pylatexenc(workdir: Path) -> None:
    (paper,) = copy_tex(workdir, "paper.tex")
    script = (
        "import json, sys\n"
        "from clearmd.frontend.cli import main\n"
        f"code = main([{str(paper)!r}, '--quiet'])\n"
        "print(json.dumps({'code': code, 'loaded': 'pylatexenc' in sys.modules}))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, timeout=120
    )
    assert json.loads(result.stdout.strip().splitlines()[-1]) == {"code": 0, "loaded": False}


@pytest.fixture
def paper_md(workdir: Path) -> str:
    (paper,) = copy_tex(workdir, "paper.tex")
    copy_tex(workdir, "img")
    assert main([str(paper), "--quiet"]) == 0
    return output(workdir, "paper.md")


def test_ac_04_title_block_and_headings(paper_md: str) -> None:
    assert paper_md.startswith("# Un artículo de prueba\n\n*Ana Pérez · 2026*")
    assert "\n## Introducción\n" in paper_md and "\n### Listas\n" in paper_md


def test_ac_05_emphasis_lists_quotes_links_footnotes_and_code(paper_md: str) -> None:
    for expected in (
        "**negrita**",
        "*itálica*",
        "- dos\n  1. anidado",
        "- **Término** Su definición.",
        "> Una cita.",
        "[un enlace](https://example.org)",
        "[^1]: Una nota al pie.",
        '```python\nprint("hola $no math$ \\section{no}")\n```',
        "`\\foo`",
    ):
        assert expected in paper_md, expected


def test_ac_06_accents_and_special_characters_become_unicode(paper_md: str) -> None:
    assert "– rango — raya “comillas”" in paper_md
    assert "comentario" not in paper_md


def test_ac_07_citations_and_references(paper_md: str) -> None:
    assert "[@knuth84; @lamport94]" in paper_md and "(eq:pit)" in paper_md


def test_ac_08_the_abstract_heading_follows_babel(paper_md: str) -> None:
    assert "## Resumen\n\nResumen breve con $x^2$." in paper_md


def test_ac_09_and_ac_10_math_is_kept_and_untouched(paper_md: str) -> None:
    assert "$E=mc^2$ y $a+b$ y $\\alpha_{i}~\\text{texto}$" in paper_md
    assert "$$\na^2+b^2=c^2\n$$" in paper_md
    assert "\\begin{aligned}\nx &= 1 \\\\ y &= 2\n\\end{aligned}" in paper_md


def test_ac_11_a_simple_table_and_its_caption(paper_md: str) -> None:
    assert "| A | B |\n|---|---|\n| 1 | $x$ |\n\n*Una tabla*" in paper_md


def test_ac_12_merged_cells_are_kept_as_latex_with_a_note(workdir: Path) -> None:
    (source,) = copy_tex(workdir, "multicolumn.tex")
    assert main([str(source), "--quiet"]) == 0
    assert "```latex\n\\begin{tabular}" in output(workdir, "multicolumn.md")
    assert "kept as LaTeX code: `1`" in summary(workdir)


def test_ac_13_a_figure_links_its_image(paper_md: str) -> None:
    assert "![Un gráfico](" in paper_md


def test_ac_18_unknown_commands_are_kept_and_reported(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (source,) = copy_tex(workdir, "unknown.tex")
    assert main([str(source)]) == 0
    assert "\\customcommand{x}" in output(workdir, "unknown.md")
    assert "unknown.tex — converted with notes" in capsys.readouterr().err
    notes = summary(workdir).split("## Converted with notes\n", 1)[1]
    assert "`\\customcommand`, `\\otherthing`, `\\begin{weirdenv}`" in notes


def test_ac_19_notes_follow_the_language(workdir: Path) -> None:
    (source,) = copy_tex(workdir, "unknown.tex")
    assert main([str(source), "--lang", "es", "--quiet"]) == 0
    assert "## Convertidos con notas" in summary(workdir)
    assert "se dejaron tal cual comandos que ClearMD no conoce" in summary(workdir)


def test_ac_20_latin1_documents_keep_their_accents(workdir: Path) -> None:
    declared, undeclared = copy_tex(workdir, "latin1.tex", "latin1_undeclared.tex")
    assert main([str(declared), str(undeclared), "--quiet"]) == 0
    assert "Cañón, acción y ñandú" in output(workdir, "latin1.md")
    assert "Cañón, acción y ñandú" in output(workdir, "latin1_undeclared.md")
    notes = summary(workdir).split("## Converted with notes\n", 1)[1]
    assert "`latin1_undeclared.tex`" in notes and "`latin1.tex`" not in notes


def test_ac_21_malformed_latex_converts_with_a_note(workdir: Path) -> None:
    (source,) = copy_tex(workdir, "malformed.tex")
    assert main([str(source), "--quiet"]) == 0
    assert "fixture-tex-malformed" in output(workdir, "malformed.md")
    assert "the LaTeX has errors" in summary(workdir)
