"""Replace a result only if its original changed (feature 028, AC-04): Settings' fourth choice
and Review's third answer, which reaches the presenter as "changed"."""

from pathlib import Path
from typing import Any

import pytest
from support.gui_close import shut
from support.gui_fakes import FakeBackend, planned
from support.ttk_unit import pump

from clearmd.backend.schemas.models import BatchPlan
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views import dialogs

CHANGED = "Replace it if the original changed"


def test_settings_round_trips_the_changed_choice(app: TtkApp) -> None:
    app.presenter.go_to(1)
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    dialog = app.dialog
    assert isinstance(dialog, dialogs.settings.SettingsDialog)
    choices = dialog._choices["on_existing_output"]
    assert list(choices) == ["ask", "overwrite", "skip", "changed"]  # after skip
    assert choices["changed"] == CHANGED
    dialog.values["on_existing_output"].set(CHANGED)
    dialog.save()
    pump(app, seconds=0.1)
    assert app.presenter.settings.on_existing_output == "changed"
    app.rail.settings.invoke()
    pump(app, seconds=0.2)
    assert isinstance(app.dialog, dialogs.settings.SettingsDialog)
    assert app.dialog.values["on_existing_output"].get() == CHANGED
    app.dialog.close()


@pytest.mark.parametrize(
    ("answer", "sent"), [("keep", False), ("overwrite", True), ("changed", "changed")]
)
def test_review_s_answer_reaches_the_presenter(
    display: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, answer: str, sent: Any
) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.docx", exists=True)), (), ())
    app = TtkApp(FakeBackend(plan=plan, settings=Settings(show_welcome=False, theme="light")))
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.presenter.analyze()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        app.presenter.go_to(2)
        pump(app, seconds=0.05)
        review = app.review
        assert review.existing.winfo_ismapped()  # the setting is "ask"
        assert review.changed.cget("text") == "Only if the original changed"
        places = [
            (int(b.grid_info()["row"]), int(b.grid_info()["column"]))
            for b in (review.keep, review.overwrite, review.changed)
        ]
        assert places == sorted(places)  # Keep, Replace, then the third (one row or wrapped)
        {"keep": review.keep, "overwrite": review.overwrite, "changed": review.changed}[
            answer
        ].invoke()
        seen: list[Any] = []
        monkeypatch.setattr(
            app.presenter, "press_primary", lambda overwrite=None: seen.append(overwrite)
        )
        app.primary_button.press()
        assert seen == [sent]
    finally:
        shut(app)
