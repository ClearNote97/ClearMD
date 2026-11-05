"""presenter/chrome (ADR-0039): the decisions every GUI's window shares, checked as tables, so
ttk, PySide6 and flet show the same header, the same second button and close the same way."""

import pytest

import clearmd.frontend.presenter.chrome.primary_gate as gate
from clearmd.frontend.presenter.chrome.close_policy import CloseStep, keep_waiting, on_close
from clearmd.frontend.presenter.chrome.header import header_of
from clearmd.frontend.presenter.chrome.secondary import SecondaryKind, ready_line, secondary_of
from clearmd.frontend.presenter.models import PlanView, Primary, Stat, StateView, Tone
from clearmd.frontend.presenter.state import Action, AppState, enabled_actions, step_of
from clearmd.i18n import load_catalog

EN = load_catalog("en")


def view(state: AppState, page: int, *, results: bool = True) -> StateView:
    enabled = enabled_actions(state, has_inputs=True, can_confirm=True, has_results=results)
    label = EN.text(f"gui.state.{state.value}")
    return StateView(state, label, enabled, step_of(state), page, Primary("", False))


def test_the_header_names_the_step_and_the_state_unless_ready() -> None:
    ready = header_of(EN, view(AppState.READY, 1), None)
    assert ready.eyebrow == EN.text("gui.steps.counter", step=1, total=4)
    assert ready.title == EN.text("gui.page.choose_title")
    assert ready.subtitle == EN.text("gui.page.choose_subtitle")
    waiting = header_of(EN, view(AppState.WAITING_DECISION, 2), None)
    assert waiting.eyebrow.endswith(" · " + EN.text("gui.state.waiting_decision"))
    assert header_of(EN, view(AppState.ANALYZING, 1), "Found 12").subtitle == "Found 12"


@pytest.mark.parametrize(
    ("state", "page", "results", "kind", "back_to"),
    [
        (AppState.ANALYZING, 1, False, SecondaryKind.CANCEL, 0),
        (AppState.CONVERTING, 3, False, SecondaryKind.CANCEL, 0),
        (AppState.WAITING_DECISION, 2, False, SecondaryKind.BACK, 1),
        (AppState.WAITING_DECISION, 3, False, SecondaryKind.BACK, 2),
        (AppState.FINISHED, 4, True, SecondaryKind.AGAIN, 0),
        (AppState.FINISHED, 4, False, SecondaryKind.NONE, 0),
        (AppState.READY, 1, False, SecondaryKind.NONE, 0),
        (AppState.READY, 4, False, SecondaryKind.NONE, 0),
    ],
)
def test_the_second_button(
    state: AppState, page: int, results: bool, kind: SecondaryKind, back_to: int
) -> None:
    second = secondary_of(EN, view(state, page), has_result=results)
    assert (second.kind, second.back_to) == (kind, back_to)
    assert second.strong is (kind is SecondaryKind.AGAIN)
    assert bool(second.text) is (kind is not SecondaryKind.NONE)


def test_the_ready_line_counts_what_will_be_converted() -> None:
    plan = PlanView("", (), False, (Stat("", 6, Tone.ACCENT),))
    assert ready_line(EN, plan) == EN.text("gui.convert.ready", count=6)
    assert ready_line(EN, None) is None and ready_line(None, plan) is None
    assert ready_line(EN, PlanView("", (), False, ())) is None


def test_the_primary_gate_reads_its_pause_when_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "PRIMARY_PAUSE_SECONDS", 0.5)
    assert not gate.gate_open(10.0, 10.4) and gate.gate_open(10.0, 10.5)
    assert gate.pause_milliseconds() == 500
    monkeypatch.setattr(gate, "PRIMARY_PAUSE_SECONDS", 0.0)
    assert gate.gate_open(10.0, 10.0) and gate.pause_milliseconds() == 0


def test_closing_waits_only_for_a_batch() -> None:
    assert on_close(AppState.CONVERTING) is CloseStep.CANCEL_AND_WAIT
    assert on_close(AppState.ANALYZING) is CloseStep.CANCEL_THEN_NOW
    assert {on_close(None), on_close(AppState.READY), on_close(AppState.FINISHED)} == {
        CloseStep.NOW
    }
    assert keep_waiting(AppState.CONVERTING, 59.9) and not keep_waiting(AppState.CONVERTING, 60)
    assert not keep_waiting(AppState.CANCELLED, 0.0)


def test_the_enabled_actions_are_the_presenters() -> None:
    assert Action.BACK in view(AppState.FINISHED, 4).enabled
