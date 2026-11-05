"""Security audit and code review of 007 (F-*, N-*, I-*, C7-*)."""

from dataclasses import replace
from pathlib import Path

from support.presenter_fakes import converted, make, state

from clearmd.frontend.presenter import AppState


def test_n1_next_on_choose_after_a_batch_starts_a_new_plan() -> None:
    presenter, view, fake, _ = converted()
    presenter.go_to(1)
    presenter.press_primary()
    view.drain()
    assert len(fake.plan_calls) == 2 and state(view).page == 2


def test_f2_each_plan_has_its_own_id() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    first = view.last("plan").plan_id
    presenter.go_to(1)
    presenter.add_paths([Path("/more")])
    presenter.remove_input(Path("/more"))
    presenter.press_primary()
    view.drain()
    assert view.last("plan").plan_id != first  # same rows, another plan: the answer resets


def test_i1_a_setting_that_changes_the_plan_drops_it() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.save_settings(replace(presenter.settings, language="es"))
    assert state(view).state is AppState.WAITING_DECISION  # the language changes no plan
    presenter.save_settings(replace(presenter.settings, recursive=False))
    assert state(view).state is AppState.READY


# --- Code review of 007 (C7-*) -------------------------------------------------------------------


def test_c7_1_an_edit_that_drops_the_plan_tells_the_view() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.add_paths([Path("/more")])
    assert "forget" in [call for call, _ in view.calls]


def test_c7_3_many_inputs_are_removed_at_once() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path(f"/docs/{n}.pdf") for n in range(50)])
    before = len(view.calls)
    presenter.remove_inputs([Path(f"/docs/{n}.pdf") for n in range(49)])
    assert [row.name for row in view.last("inputs")] == ["49.pdf"]
    assert len([call for call, _ in view.calls[before:] if call == "inputs"]) == 1


def test_c7_4_an_edit_that_changes_nothing_keeps_the_plan() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.add_paths([Path("/docs")])  # already listed
    presenter.remove_input(Path("/not-listed"))
    presenter.choose_output_next_to()  # already next to the originals
    assert state(view).state is AppState.WAITING_DECISION
