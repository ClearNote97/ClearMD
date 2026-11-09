"""Regressions of the code review and the security audit of 005 (C-*, S-*, A-*)."""

from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from support.gui_fakes import FakeBackend, planned
from support.presenter_fakes import FakeView, absolute, converted, make

from clearmd.backend.schemas.models import (
    BatchPlan,
)
from clearmd.backend.schemas.settings import Settings, SettingsProblem, SettingsWarning
from clearmd.frontend.presenter import AppState, Presenter


def calls_after(view: FakeView, name: str) -> list[str]:
    """The calls made after the last ``name`` call."""
    index = max(i for i, (call, _) in enumerate(view.calls) if call == name)
    return [call for call, _ in view.calls[index + 1 :]]


def test_c2_an_unexpected_error_is_told_after_the_state_changes() -> None:
    presenter, view, _, _ = make(FakeBackend(plan_error=RuntimeError("boom")))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert "state" not in calls_after(view, "message")  # a step change would wipe it in a view
    message = view.last("message")
    assert "what was already converted is kept" in message  # C-13: true after a partial batch


def test_c3_start_up_warnings_come_after_the_first_state_in_one_message() -> None:
    warnings = (
        SettingsWarning("colour", SettingsProblem.UNKNOWN_KEY),
        SettingsWarning("theme", SettingsProblem.INVALID_VALUE),
    )
    _, view, _, _ = make(FakeBackend(warnings=warnings))
    assert "state" not in calls_after(view, "message")
    shown = view.last("message")
    assert "colour" in shown and "theme" in shown


def held() -> tuple[Presenter, FakeView, FakeBackend, list[Callable[[], None]]]:
    """A presenter whose work never runs until released: it stays ANALYZING or CONVERTING."""
    view, fake = FakeView(), FakeBackend()
    waiting: list[Callable[[], None]] = []
    presenter = Presenter(view, fake, detect_theme=lambda: "light", spawn=waiting.append)
    presenter.start()
    view.drain()
    return presenter, view, fake, waiting


def test_c4_inputs_and_the_output_cannot_change_while_analyzing() -> None:
    presenter, view, _, _ = held()
    presenter.add_paths([Path("/docs/a.pdf"), Path("/docs/b.pdf")])
    presenter.analyze()
    assert presenter.state is AppState.ANALYZING
    presenter.remove_input(Path("/docs/a.pdf"))
    presenter.clear_inputs()
    presenter.add_paths([Path("/docs/c.pdf")])
    presenter.choose_output_folder(Path("/elsewhere"))
    assert [row.name for row in view.last("inputs")] == ["a.pdf", "b.pdf"]
    assert presenter.output_folder is None


def test_c5_the_result_follows_a_language_change() -> None:
    presenter, view, fake, _ = converted()
    presenter.save_settings(replace(fake.settings, language="es"))
    assert view.last("result").stats[0].label == "Convertido"  # one: the singular (audit v3, F5-07)


def test_c5_the_theme_is_applied_only_when_it_changes() -> None:
    presenter, view, fake, _ = make()
    themes = len([call for call, _ in view.calls if call == "theme"])
    presenter.save_settings(replace(fake.settings, language="es"))
    assert len([call for call, _ in view.calls if call == "theme"]) == themes


def test_c6_scan_progress_reaches_the_view_at_most_every_100_ms() -> None:
    from clearmd.backend.schemas.events import ScanProgress

    class Scanning(FakeBackend):
        def plan_batch(self, inputs: Sequence[Path], **kwargs: Any) -> BatchPlan:
            for found in range(500):
                kwargs["on_event"](ScanProgress(found=found, current=Path("/docs")))
            return super().plan_batch(inputs, **kwargs)

    presenter, view, _, _ = make(Scanning())
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain(timers=True)
    view.drain()
    scans = [value for call, value in view.calls if call == "scan"]
    assert len(scans) <= 3  # started, and the latest count once


def test_c8_cancelling_an_analysis_stops_the_scan() -> None:
    presenter, _, fake, waiting = held()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    presenter.cancel()
    waiting.pop()()  # the worker runs now: its token was cancelled
    assert fake.plan_calls[-1]["cancel"].is_set()


def test_c12_every_folder_that_cannot_be_opened_is_told_in_one_message() -> None:
    class Unopenable(FakeBackend):
        def open_folder(self, path: Path) -> None:
            raise OSError("no file browser")

    plan = BatchPlan((planned("a.pdf"), planned("b.pdf", folder=Path("/other"))), (), ())
    presenter, view, _, _ = converted(Unopenable(plan=plan))
    presenter.open_results()
    shown = view.last("message")
    assert (
        str(Path("/docs/ClearMD_Output")) in shown and str(Path("/other/ClearMD_Output")) in shown
    )


def test_s1_a_folder_that_cannot_be_remembered_is_used_but_not_saved() -> None:
    presenter, _, fake, _ = make()
    odd = Path("/tmp/a\nb")
    presenter.choose_output_folder(odd)
    assert presenter.output_folder == absolute(str(odd))  # the results still go there
    assert all("\n" not in saved.last_output_folder for saved in fake.saved)
    presenter.save_settings(replace(presenter.settings, language="es"))
    assert fake.saved[-1].language == "es"  # later saves are not blocked


def test_s2_names_are_shown_with_invisible_characters_escaped() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs/x‮gpj.exe"), Path("/docs/a\nb.pdf")])
    names = [row.name for row in view.last("inputs")]
    assert names == ["x\\u202egpj.exe", "a\\nb.pdf"] or all(
        "‮" not in name and "\n" not in name for name in names
    )


# --- Adversarial verification of the fixes (A-*) -------------------------------------------------


def test_a1_a_window_closing_never_opens_the_results_afterwards() -> None:
    fake = FakeBackend(settings=Settings(open_output_when_done=True))
    presenter, view, _, _ = make(fake)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.shutdown()  # the window is closing: the batch may still finish normally
    presenter.confirm()
    view.drain()
    assert view.last("state").state is AppState.FINISHED
    assert fake.opened == []


def test_a2_a_cancelled_analysis_never_swallows_the_next_ones_count() -> None:
    presenter, view, _, _ = held()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    presenter._analysis.scanned(presenter._session.generation, 7)  # a count arrives: timer pending
    presenter.cancel()
    presenter.analyze()
    presenter._analysis.scanned(presenter._session.generation, 1234)  # the new analysis's count
    for _ in range(3):
        view.drain(timers=True)  # the old timer fires first
    scans = [value for call, value in view.calls if call == "scan"]
    assert any("1234" in text for text in scans)
