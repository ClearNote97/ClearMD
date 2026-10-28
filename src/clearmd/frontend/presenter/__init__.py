"""Presenter (MVP): the interaction logic shared by every GUI (feature 005, ADR-0026).

A GUI implements ``ports.View`` and calls the presenter's intents; the presenter owns the state
and every text. Standard library only: no toolkit is ever imported here.
"""

from clearmd.frontend.presenter.models import OutputMode
from clearmd.frontend.presenter.presenter import Presenter
from clearmd.frontend.presenter.state import Action, AppState

__all__ = ["Action", "AppState", "OutputMode", "Presenter"]
