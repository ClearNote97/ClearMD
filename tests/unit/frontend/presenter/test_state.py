"""The seven states and what each enables (005, T03; AC-01)."""

from pathlib import Path

from support.presenter_fakes import make

from clearmd.frontend.presenter import Action, AppState


def test_it_starts_ready_with_convert_disabled_until_there_are_inputs() -> None:
    presenter, view, _, _ = make()
    state = view.last("state")
    assert state.state is AppState.READY and state.label == "Ready"
    assert not {Action.CONVERT, Action.REMOVE, Action.CANCEL} & state.enabled
    assert {Action.ADD, Action.HELP, Action.SETTINGS} <= state.enabled
    presenter.add_paths([Path("/docs/a.pdf")])
    assert {Action.CONVERT, Action.REMOVE} <= view.last("state").enabled


def test_each_state_enables_only_its_actions() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    analyzing = view.last("state")
    assert analyzing.state is AppState.ANALYZING
    assert analyzing.enabled == {Action.CANCEL, Action.HELP}
    view.drain()
    waiting = view.last("state")
    assert waiting.state is AppState.WAITING_DECISION
    editing = {Action.ADD, Action.REMOVE, Action.CHOOSE_OUTPUT, Action.SETTINGS}
    assert waiting.enabled == {Action.CONFIRM, Action.BACK, Action.HELP} | editing  # ADR-0029


def test_the_seven_states_have_their_labels_in_both_languages() -> None:
    from clearmd.i18n import load_catalog

    for language in ("en", "es"):
        catalog = load_catalog(language)
        labels = {catalog.text(f"gui.state.{state.value}") for state in AppState}
        assert len(labels) == 7
