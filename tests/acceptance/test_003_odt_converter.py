"""Feature 003 — one test per acceptance criterion (spec/features/003_*/spec.md)."""

import json
import shutil
import time
from pathlib import Path

import pytest
from build_fixtures import ODT_AUTOMATIC_STYLES, _odt_xml, odt_package
from support import ODT_DIR
from support.markdown_guarantee import broken_promises

from clearmd.frontend.cli import main


def copy_odt(workdir: Path, *names: str) -> list[Path]:
    copies = []
    for name in names:
        target = workdir / Path(name).name
        shutil.copyfile(ODT_DIR / name, target)
        copies.append(target)
    return copies


def output(workdir: Path, name: str) -> str:
    return (workdir / "ClearMD_Output" / "OutputMD" / name).read_text(encoding="utf-8")


def summary(workdir: Path) -> str:
    return (workdir / "ClearMD_Output" / "Resumen_ClearMD.md").read_text(encoding="utf-8")


@pytest.fixture
def report_md(workdir: Path) -> str:
    (report,) = copy_odt(workdir, "report.odt")
    assert main([str(report), "--quiet"]) == 0
    return output(workdir, "report.md")


# --- Through the pipeline ------------------------------------------------------------------------


def test_ac_01_an_odt_converts_through_the_pipeline(workdir: Path) -> None:
    (report,) = copy_odt(workdir, "report.odt")
    assert main([str(report), "--quiet"]) == 0
    assert "fixture-odt-report" in output(workdir, "report.md")
    assert "| `report.odt` | — | `report.md` | ODT |" in summary(workdir)


def test_ac_02_an_odt_without_extension_is_detected_by_content(workdir: Path) -> None:
    (source,) = copy_odt(workdir, "no_extension_odt")
    assert main([str(source), "--quiet"]) == 0
    assert "fixture-odt-report" in output(workdir, "no_extension_odt.md")
    assert "ODT, detected by content" in summary(workdir)


def test_ac_03_an_odt_zip_bomb_is_skipped_before_anything_is_read(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bomb, good = copy_odt(workdir, "hostile/bomb.odt", "report.odt")
    assert main([str(bomb), str(good)]) == 0
    assert "Skipped: bomb.odt — " in capsys.readouterr().err
    assert not (workdir / "ClearMD_Output" / "OutputMD" / "bomb.md").exists()
    assert (workdir / "ClearMD_Output" / "OutputMD" / "report.md").is_file()


def test_ac_04_what_cannot_be_converted_says_why_and_the_batch_goes_on(workdir: Path) -> None:
    sources = copy_odt(workdir, "spreadsheet.odt", "encrypted.odt", "damaged.odt", "report.odt")
    assert main([*map(str, sources), "--quiet"]) == 1
    text = summary(workdir)
    assert "ClearMD cannot convert this kind of file" in text
    assert "This file is password-protected." in text
    assert "This file seems to be damaged." in text
    assert (workdir / "ClearMD_Output" / "OutputMD" / "report.md").is_file()


# --- Structure and text --------------------------------------------------------------------------


def test_ac_05_title_subtitle_and_headings(report_md: str) -> None:
    assert report_md.startswith("# Informe de prueba\n\n*Un subtítulo*\n\n## Introducción")
    assert "\n### Listas y enlaces\n" in report_md and "\n#### Tabla\n" in report_md


def test_ac_06_emphasis_from_automatic_named_and_parent_styles(report_md: str) -> None:
    for expected in (
        "**negrita**",
        "*itálica*",
        "<u>subrayado</u>",
        "~~tachado~~",
        "m<sup>2</sup>",
        "H<sub>2</sub>O",
        "`código`",
        "*énfasis*",
        "**fuerte**",
        "***ambos***",
    ):
        assert expected in report_md, expected


def test_ac_07_lists_links_notes_quotations_and_code(report_md: str) -> None:
    for expected in (
        "- dos\n  1. anidado",
        "3. tres\n4. cuatro",
        "[enlace](https://example.org)",
        "una nota.[^1] Y otra al final.[^2]",
        "[^2]: Una nota final.",
        "> Una cita.",
        "```\ndef f(x):\n    return x\n```",
    ):
        assert expected in report_md, expected


def test_ac_08_spaces_fields_hidden_and_generated_content(report_md: str) -> None:
    assert "a   b\tc  \nd" in report_md
    assert "Página 7 del 25/10/2026." in report_md
    assert "oculto" not in report_md and "....." not in report_md


# --- Tables, images and formulas -----------------------------------------------------------------


def test_ac_09_tables_with_a_header_and_merged_cells_simplified(
    workdir: Path, report_md: str
) -> None:
    assert "| A | B |\n|---|---|\n| 1 | **2** |" in report_md
    (merged,) = copy_odt(workdir, "merged.odt")
    assert main([str(merged), "--quiet"]) == 0
    assert "| Junta |  |" in output(workdir, "merged.md")
    assert "tables with merged cells were simplified" in summary(workdir)


def test_ac_10_images_are_placeholders_and_nothing_else_is_written(workdir: Path) -> None:
    (images,) = copy_odt(workdir, "images.odt")
    assert main([str(images), "--quiet"]) == 0
    assert "*Image: Mapa de la región*" in output(workdir, "images.md")
    assert "images stay inside the document and are shown by their title: `3`" in summary(workdir)
    written = sorted(p.name for p in (workdir / "ClearMD_Output").rglob("*") if p.is_file())
    assert written == ["Resumen_ClearMD.md", "images.md"]


def test_ac_11_formulas_in_the_subset_become_latex(workdir: Path) -> None:
    (real,) = copy_odt(workdir, "real/report.odt")
    assert main([str(real), "--quiet"]) == 0
    text = output(workdir, "report.md")
    assert "$$\n\\frac{a}{b}+x^{2}+\\sqrt{y}+\\alpha\n$$" in text
    assert "$\\sum_{i=1}^{n}i$" in text and "\\hat{x}" in text


def test_ac_12_a_formula_outside_the_subset_keeps_its_starmath_source(workdir: Path) -> None:
    (formulas,) = copy_odt(workdir, "formulas.odt")
    assert main([str(formulas), "--quiet"]) == 0
    assert "Fuera: `boxed z`." in output(workdir, "formulas.md")
    assert "shown as their StarMath source: `2`" in summary(workdir)


# --- Honesty -------------------------------------------------------------------------------------


def test_ac_13_comments_and_tracked_changes_give_the_final_text(workdir: Path) -> None:
    (revisions,) = copy_odt(workdir, "revisions.odt")
    assert main([str(revisions), "--quiet"]) == 0
    assert "borrado" not in output(workdir, "revisions.md")
    assert "the text is the final one: `1` (comments), `1` (tracked changes)" in summary(workdir)


def test_ac_14_unknown_elements_keep_their_text_and_are_listed(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (unknown,) = copy_odt(workdir, "unknown.odt")
    assert main([str(unknown)]) == 0
    assert "texto en forma" in output(workdir, "unknown.md")
    assert "unknown.odt — converted with notes" in capsys.readouterr().err
    assert "kept only their text: `draw:custom-shape`, `text:ruby`" in summary(workdir)


def test_ac_15_notes_follow_the_language(workdir: Path) -> None:
    (revisions,) = copy_odt(workdir, "revisions.odt")
    assert main([str(revisions), "--lang", "es", "--quiet"]) == 0
    text = summary(workdir)
    assert "## Necesita tu atención" in text
    assert "`1` (comentarios), `1` (cambios rastreados)" in text


# --- Safety --------------------------------------------------------------------------------------


def test_ac_16_a_doctype_or_entities_refuse_the_file(workdir: Path) -> None:
    sources = copy_odt(workdir, "hostile/doctype.odt", "hostile/entities.odt")
    started = time.monotonic()
    assert main([*map(str, sources), "--quiet"]) == 1
    assert time.monotonic() - started < 60
    assert summary(workdir).count("This file seems to be damaged.") == 2


def test_ac_17_parts_over_the_limits_are_refused_quickly(
    workdir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # 20,000 nested spans compress so well that the archive check of feature 001 skips the file
    # before its XML is read; the XML limits themselves are covered by test_xmltree.py.
    deep, wide = copy_odt(workdir, "hostile/deep.odt", "hostile/many_elements.odt")
    started = time.monotonic()
    main([str(deep), str(wide)])
    assert time.monotonic() - started < 60
    assert "Skipped: deep.odt — " in capsys.readouterr().err
    assert not (workdir / "ClearMD_Output" / "OutputMD" / "deep.md").exists()


def test_ac_18_the_output_guarantee_holds_through_the_cli(workdir: Path) -> None:
    hostile = (
        "<text:p>&lt;img src=x&gt; ![x](http://evil.example/b.png) "
        '<text:span text:style-name="T7">``&lt;img&gt;</text:span></text:p>'
        "<text:p># no</text:p><text:p>===</text:p>"
    )
    source = workdir / "hostile.odt"
    source.write_bytes(
        odt_package(_odt_xml("document-content", hostile, automatic=ODT_AUTOMATIC_STYLES))
    )
    assert main([str(source), "--quiet"]) == 0
    assert broken_promises(output(workdir, "hostile.md")) == []


def test_ac_19_objects_outside_the_archive_are_never_read(workdir: Path) -> None:
    (formulas,) = copy_odt(workdir, "formulas.odt")
    assert main([str(formulas), "--quiet"]) == 0
    assert "Afuera: *Formula*." in output(workdir, "formulas.md")


# --- Measured ------------------------------------------------------------------------------------


def test_ac_20_the_odt_speed_and_memory_are_the_measured_ones() -> None:
    from clearmd.backend.schemas.formats import FormatId
    from clearmd.backend.schemas.limits import MEMORY_PER_MIB, SECONDS_PER_MIB

    results = Path(__file__).parents[2] / "docs" / "benchmarks" / "003-results.json"
    rows = [row for row in json.loads(results.read_text("utf-8"))["rows"] if row["result"]["ok"]]
    text_mib = [row["archive"]["uncompressed_mib"] for row in rows]
    speed = max(row["result"]["seconds"] / mib for row, mib in zip(rows, text_mib, strict=True))
    memory = max(
        (row["result"]["peak_mib"] - row["result"]["baseline_mib"]) / mib
        for row, mib in zip(rows, text_mib, strict=True)
        if mib >= 5
    )
    assert speed <= SECONDS_PER_MIB[FormatId.ODT] <= 1.5 * speed
    assert memory <= MEMORY_PER_MIB[FormatId.ODT] <= 1.5 * memory
