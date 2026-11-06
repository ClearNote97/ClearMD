"""What the window shows now: the last state, plan, progress and result the presenter gave, the
language, the theme and the scan text. A module of its own: the view writes it, and the dialogs,
pickers, keys and closing read it without knowing the view."""

from dataclasses import dataclass

from clearmd.frontend.design.palette import LIGHT, Palette
from clearmd.frontend.presenter import Action
from clearmd.frontend.presenter.models import PlanView, ProgressView, ResultView, StateView
from clearmd.i18n import Catalog


@dataclass
class Shown:
    state: StateView | None = None
    last_plan: PlanView | None = None
    last_progress: ProgressView | None = None
    last_result: ResultView | None = None
    catalog: Catalog | None = None
    palette: Palette = LIGHT
    scan: str | None = None  # the text shown while a scan runs

    def allows(self, action: Action) -> bool:
        return self.state is None or action in self.state.enabled

    def need_catalog(self) -> Catalog:
        if self.catalog is None:
            raise RuntimeError("the presenter has not started")
        return self.catalog
