"""Feature 033 — "What Next?" as the three tools and one box for the files
(spec/features/033_*/spec.md): the presenter and its texts."""

from pathlib import Path

import pytest
from support.presenter_fakes import converted, make

from clearmd.frontend.presenter.state import AppState, Tool
from clearmd.i18n import load_catalog


@pytest.mark.parametrize("used", list(Tool))
def test_ac_01_the_tool_just_used_first_then_the_others(used: Tool) -> None:
    presenter, _, _, _ = make()
    presenter.choose_tool(used)
    choices = presenter.next_choices()
    assert choices[0].tool is used and choices[0].current
    assert [choice.tool for choice in choices[1:]] == [tool for tool in Tool if tool is not used]
    assert not any(choice.current for choice in choices[1:])


def test_ac_01_titles() -> None:
    presenter, _, _, _ = make()
    assert [choice.title for choice in presenter.next_choices()] == [
        "Convert Again",
        "Split",
        "Merge",
    ]


@pytest.mark.parametrize("keep", [True, False])
@pytest.mark.parametrize("tool", list(Tool))
def test_ac_01_and_02_one_click_opens_step_1_with_or_without_the_files(
    tool: Tool, keep: bool
) -> None:
    presenter, view, _, _ = converted()
    presenter.continue_with(tool, keep=keep)
    view.drain()
    assert (presenter.page, presenter.tool, presenter.state) == (1, tool, AppState.READY)
    assert bool(view.last("inputs")) is keep


def test_ac_02_nothing_happens_while_working() -> None:
    presenter, view, _, _ = make(threaded=True)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()  # still analysing: the threaded fake has not answered
    assert presenter.state in (AppState.ANALYZING,)
    presenter.continue_with(Tool.SPLIT, keep=False)
    assert presenter.tool is Tool.CONVERT
    view.drain()


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_03_texts(language: str) -> None:
    catalog = load_catalog(language)
    expected = {
        "en": ("What Next?", "Convert Again", "Keep the files you chose", "Cancel"),
        "es": (
            "¿Qué Sigue?",
            "Convertir Otra Vez",
            "Conservar los archivos que elegiste",
            "Cancelar",
        ),
    }[language]
    again = catalog.text("gui.more.again", tool=catalog.text("gui.more.convert"))
    got = (
        catalog.text("gui.more.title"),
        again,
        catalog.text("gui.more.keep"),
        catalog.text("gui.more.cancel"),
    )
    assert got == expected
    assert catalog.text("gui.more.keep_help")
