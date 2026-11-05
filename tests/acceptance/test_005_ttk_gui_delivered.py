"""Feature 005 — Delivered (AC-20 to AC-23); spec/features/005_*/spec.md.

The window runs under a display (a virtual one when there is none), mostly on a fake backend.
"""

import tomllib
from collections.abc import Callable
from pathlib import Path

from support.gui_fakes import FakeBackend, MemoryBackend, planned
from support.ttk_acceptance import (
    QUIET,
    ROOT,
    confirm,
    converted,
    copy_documents,
    pump,
    replace_settings,
    to_review,
)

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.frontend.cli import main as cli_main
from clearmd.frontend.presenter.icons import ICONS
from clearmd.frontend.ttk import TtkApp


def test_ac_20_clearmd_ttk_starts_the_gui_and_converts_like_the_cli(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert scripts["project"]["gui-scripts"]["clearmd-ttk"] == "clearmd.frontend.ttk:main"
    names = ("sample.docx", "sample.csv", "sample.txt", "encrypted.pdf")
    by_gui = copy_documents(tmp_path / "gui" / "Docs", *names)
    by_cli = copy_documents(tmp_path / "cli" / "Docs", *names)
    app = window(MemoryBackend(QUIET))
    to_review(app, by_gui)
    confirm(app)
    pump(app, until=lambda: converted(app), seconds=120)
    cli_main([str(by_cli), "--quiet"])

    def outputs(root: Path) -> dict[str, str]:
        out = root / "ClearMD_Output" / "OutputMD"
        return {str(p.relative_to(out)): p.read_text(encoding="utf-8") for p in out.rglob("*.md")}

    assert outputs(tmp_path / "gui") == outputs(tmp_path / "cli") != {}
    summaries = [
        (root / "ClearMD_Output" / "Resumen_ClearMD.md").read_text(encoding="utf-8")
        for root in (tmp_path / "gui", tmp_path / "cli")
    ]
    tables = [[line for line in text.splitlines() if line.startswith("| `")] for text in summaries]
    assert tables[0] == tables[1] != []


def test_ac_21_screenshots_of_every_screen_light_and_dark_english_and_spanish() -> None:
    shots = ROOT / "docs" / "screenshots" / "005"
    screens = (
        "0-welcome",
        "1-choose",
        "2-review",
        "3-convert",
        "4-results",
        "5-help",
        "6-settings",
    )
    for screen in screens:
        for theme in ("light", "dark"):
            for language in ("en", "es"):
                assert (shots / f"{screen}-{theme}-{language}.png").is_file()


def test_ac_22_the_window_wears_clearmds_identity(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(settings=replace_settings(QUIET, theme="dark")))
    assert app.style.theme_use() == "clearmd-dark"
    assert app.rail.step_texts() == ["> Choose", "Review", "Convert", "Results"]
    assert {"Primary.ClearMD.TButton.face", "Card.ClearMD.face"} <= set(app.style.element_names())
    assert [icon.width() for icon in app.icons] == [16, 32, 48, 64, 128, 256]


def test_ac_23_every_list_shows_number_icon_and_name(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.docx")),
        (SkippedItem(Path("/docs/n.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    app = window(FakeBackend(plan=plan, statuses={"a.pdf": OutcomeStatus.FAILED}, settings=QUIET))
    app.presenter.add_paths([tmp_path])
    lists = [app.main.inputs]
    to_review(app, tmp_path)
    lists.append(app.review.files)
    assert [row.icon for row in app.last_plan.rows] == ["pdf", "docx", "markdown"]  # type: ignore[union-attr]
    confirm(app)
    pump(app, until=lambda: converted(app))
    lists.append(app.results.problems)
    for file_list in lists:
        tree = file_list.tree
        assert tree.get_children() and all(tree.item(i, "image") for i in tree.get_children())
    icons = ROOT / "src" / "clearmd" / "frontend" / "assets" / "icons"
    assert all((icons / f"{name}.png").is_file() for name in ICONS)
