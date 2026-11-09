"""The action bar's second button (ADR-0029): Cancel while working, Back on Review and Convert,
Convert more on Results once there is a result; and the line Convert shows before it starts."""

from dataclasses import dataclass
from enum import StrEnum

from clearmd.frontend.presenter.models import PlanView, RowKind, StateView
from clearmd.frontend.presenter.state import Action, AppState
from clearmd.i18n import Catalog


class SecondaryKind(StrEnum):
    NONE = "none"
    CANCEL = "cancel"  # presenter.cancel
    BACK = "back"  # presenter.go_to(back_to)
    AGAIN = "again"  # "Convert more": ask whether to keep the files


@dataclass(frozen=True)
class Secondary:
    kind: SecondaryKind
    text: str = ""
    strong: bool = False  # drawn as prominent as the primary action (Convert more)
    back_to: int = 0  # the page Back opens


def secondary_of(catalog: Catalog, state: StateView, *, has_result: bool) -> Secondary:
    if state.state in {AppState.ANALYZING, AppState.CONVERTING}:
        return Secondary(SecondaryKind.CANCEL, catalog.text("gui.progress.cancel"))
    if state.page in {2, 3}:
        return Secondary(SecondaryKind.BACK, catalog.text("gui.plan.back"), back_to=state.page - 1)
    if state.page == 4 and Action.BACK in state.enabled and has_result:
        return Secondary(SecondaryKind.AGAIN, catalog.text("gui.result.again"), strong=True)
    return Secondary(SecondaryKind.NONE)


def ready_line(
    catalog: Catalog | None,
    plan: PlanView | None,
    setting: str = "ask",
    answer: bool | str | None = None,
) -> str | None:
    """Convert's card before the batch (``None``: nothing to say): how many files will really be
    written, with the decision about existing results already taken (audit 2026-11-08, 2C):
    ``setting`` is Settings' "When a Result Already Exists", ``answer`` Review's choice."""
    if plan is None or catalog is None or not plan.stats:
        return None
    new = sum(1 for row in plan.rows if row.kind is RowKind.CONVERT)
    existing = sum(1 for row in plan.rows if row.kind is RowKind.EXISTS)
    if not existing:
        return catalog.text("gui.convert.ready", count=plan.stats[0].value)
    choice = setting if setting != "ask" else answer
    if choice in (True, "overwrite"):
        how, written = "replace", new + existing
    elif choice == "changed":
        how, written = "changed", new
    elif choice in (False, "keep"):
        how, written = "keep", new
    else:
        how, written = "ask", new
    lines = [catalog.text("gui.convert.ready", count=written)]
    lines.append(catalog.plural(f"gui.convert.existing_{how}", existing))
    return "\n".join(lines)
