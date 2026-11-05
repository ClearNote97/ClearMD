"""Inputs and the output choice (005, T03; AC-05, AC-06)."""

from pathlib import Path

from support.gui_fakes import FakeBackend
from support.presenter_fakes import absolute, make

from clearmd.backend.schemas.formats import Strategy
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import Action, OutputMode


def test_inputs_are_never_listed_twice_and_can_be_removed() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs/a.pdf"), Path("/docs/a.pdf"), Path("/docs/../docs/a.pdf")])
    presenter.add_paths([Path("/docs/b")])
    rows = view.last("inputs")
    assert [row.path for row in rows] == [absolute("/docs/a.pdf"), absolute("/docs/b")]
    presenter.remove_input(Path("/docs/a.pdf"))
    assert [row.path for row in view.last("inputs")] == [absolute("/docs/b")]
    presenter.clear_inputs()
    assert view.last("inputs") == ()
    assert Action.CONVERT not in view.last("state").enabled


def test_the_output_goes_next_to_the_originals_by_default() -> None:
    presenter, view, fake, _ = make()
    assert view.last("output").mode is OutputMode.NEXT_TO
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    assert fake.plan_calls[-1]["output_root"] is None


def test_a_picked_folder_is_used_and_remembered(tmp_path: Path) -> None:
    presenter, view, fake, _ = make()
    presenter.choose_output_folder(tmp_path)
    choice = view.last("output")
    assert choice.mode is OutputMode.FOLDER and choice.folder == tmp_path
    assert fake.saved[-1].last_output_folder == str(tmp_path)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    assert fake.plan_calls[-1]["output_root"] == tmp_path
    # Next time: still next to the originals by default, the folder offered as the suggestion.
    _, again, _, _ = make(FakeBackend(settings=fake.settings))
    assert again.last("output").mode is OutputMode.NEXT_TO
    assert again.last("output").suggestion == tmp_path


def test_the_settings_reach_the_plan() -> None:
    settings = Settings(recursive=False, html_strategy="article")
    presenter, _, fake, _ = make(FakeBackend(settings=settings))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    call = fake.plan_calls[-1]
    assert call["recursive"] is False and call["html_strategy"] is Strategy.ARTICLE
