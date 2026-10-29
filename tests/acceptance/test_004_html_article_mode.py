"""Feature 004 — one test per acceptance criterion (spec/features/004_*/spec.md)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from support import HTML_DIR
from support.markdown_guarantee import broken_promises

from clearmd.frontend.cli import main


def copy_html(workdir: Path, *names: str) -> list[Path]:
    copies = []
    for name in names:
        target = workdir / name
        shutil.copyfile(HTML_DIR / name, target)
        copies.append(target)
    return copies


def output(workdir: Path, name: str) -> str:
    return (workdir / "ClearMD_Output" / "OutputMD" / name).read_text(encoding="utf-8")


def summary(workdir: Path) -> str:
    return (workdir / "ClearMD_Output" / "Resumen_ClearMD.md").read_text(encoding="utf-8")


def _settings(text: str) -> None:
    from clearmd.backend.api import settings_path

    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


NOISE = ("MENU-FIXTURE", "COOKIES-FIXTURE", "ASIDE-FIXTURE", "FOOTER-FIXTURE")


@pytest.fixture
def article_md(workdir: Path) -> str:
    (page,) = copy_html(workdir, "news.html")
    assert main([str(page), "--html", "article", "--quiet"]) == 0
    return output(workdir, "news.md")


def test_ac_01_by_default_a_page_converts_in_full(workdir: Path) -> None:
    (page,) = copy_html(workdir, "news.html")
    assert main([str(page), "--quiet"]) == 0
    markdown = output(workdir, "news.md")
    assert "fixture-html-article" in markdown and "MENU-FIXTURE" in markdown
    assert "| `news.html` | — | `news.md` | HTML |" in summary(workdir)


def test_ac_02_the_setting_or_the_flag_chooses_the_article(workdir: Path) -> None:
    (page,) = copy_html(workdir, "news.html")
    _settings('html_strategy = "article"\n')
    assert main([str(page), "--quiet"]) == 0
    markdown = output(workdir, "news.md")
    assert markdown.startswith("# Estaciones comunitarias miden el cambio en el Magdalena\n")
    assert "fixture-html-article" in markdown
    assert not [noise for noise in NOISE if noise in markdown]
    assert main([str(page), "--html", "full", "--overwrite", "--quiet"]) == 0
    assert "MENU-FIXTURE" in output(workdir, "news.md")


def test_ac_03_the_summary_shows_the_strategy(workdir: Path, article_md: str) -> None:
    assert "| `news.html` | — | `news.md` | HTML (Article) |" in summary(workdir)


def test_ac_04_the_article_keeps_its_structure(article_md: str) -> None:
    for expected in (
        "## Qué miden",
        "**licencia abierta** y *formato CSV*",
        "[el repositorio del proyecto](https://example.org/estaciones)",
        "- Caudal del río\n  - en metros cúbicos por segundo",
        "1. Instalar la estación\n2. Calibrarla",
        "> Ahora sabemos cuándo sembrar",
        "| Año | Días de adelanto |\n|---|---|\n| 2016 | 4 |",
        "```\npython analizar.py --estacion honda\n```",
    ):
        assert expected in article_md, expected


def test_ac_05_images_are_placeholders_and_nothing_else_is_written(
    workdir: Path, article_md: str
) -> None:
    assert "*Imagen: Una estación junto al río*" in article_md
    assert "cdn.example.org" not in article_md and "![" not in article_md
    assert "images not downloaded (each shown by its description): `1`" in summary(workdir)
    written = sorted(p.relative_to(workdir).as_posix() for p in workdir.rglob("*") if p.is_file())
    assert written == [
        "ClearMD_Output/OutputMD/news.md",
        "ClearMD_Output/Resumen_ClearMD.md",
        "news.html",
    ]


def test_ac_06_no_article_means_the_full_page_and_a_note(workdir: Path) -> None:
    (page,) = copy_html(workdir, "no_article.html")
    assert main([str(page), "--html", "article", "--quiet"]) == 0
    assert "fixture-html-no-article" in output(workdir, "no_article.md")
    assert "no article was found in the page, so the whole page was converted" in summary(workdir)


def test_ac_07_hostile_pages_never_break_the_output_guarantee(workdir: Path) -> None:
    (page,) = copy_html(workdir, "hostile.html")
    assert main([str(page), "--html", "article", "--quiet"]) == 0
    markdown = output(workdir, "hostile.md")
    assert "fixture-html-hostile" in markdown
    assert broken_promises(markdown, blocks=frozenset({"heading_open"})) == []  # the title
    # Every place and a seeded fuzz: tests/unit/backend/services/conversion/html/.


def test_ac_08_no_network_is_used(workdir: Path) -> None:
    # The network guard is on in this process and in the worker (conftest): any fetch would fail
    # the conversion. The hostile page links an iframe, a script and a remote image.
    pages = copy_html(workdir, "news.html", "hostile.html")
    assert main([*map(str, pages), "--html", "article", "--quiet"]) == 0
    assert "## Failed" not in summary(workdir)
    assert "fixture-html-article" in output(workdir, "news.md")


def test_ac_09_notes_in_the_users_language(workdir: Path) -> None:
    (page,) = copy_html(workdir, "no_article.html")
    assert main([str(page), "--html", "article", "--lang", "es", "--quiet"]) == 0
    assert "no se encontró un artículo en la página; se convirtió la página completa" in summary(
        workdir
    )
    assert "| HTML (Artículo) |" in summary(workdir)


def test_ac_10_the_cli_process_never_imports_trafilatura(workdir: Path) -> None:
    (page,) = copy_html(workdir, "news.html")
    script = (
        "import json, sys\n"
        "from clearmd.frontend.cli import main\n"
        f"code = main([{str(page)!r}, '--html', 'article', '--quiet'])\n"
        "print(json.dumps({'code': code, 'loaded': 'trafilatura' in sys.modules}))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True, timeout=120
    )
    assert json.loads(result.stdout.strip().splitlines()[-1]) == {"code": 0, "loaded": False}


def test_ac_11_the_benchmark_measures_the_article_strategy() -> None:
    from clearmd.backend.schemas.limits import ARTICLE_MEMORY_PER_MIB, ARTICLE_SECONDS_PER_MIB

    results = Path(__file__).parents[2] / "docs" / "benchmarks" / "004-results.json"
    rows = [row for row in json.loads(results.read_text("utf-8"))["rows"] if row["result"]["ok"]]
    assert max(row["size_mib"] for row in rows) >= 25
    speed = max(row["result"]["seconds"] / row["size_mib"] for row in rows)
    memory = max(
        (row["result"]["peak_mib"] - row["result"]["baseline_mib"]) / row["size_mib"]
        for row in rows
    )
    assert speed <= ARTICLE_SECONDS_PER_MIB <= 1.5 * speed
    assert memory <= ARTICLE_MEMORY_PER_MIB <= 1.5 * memory
