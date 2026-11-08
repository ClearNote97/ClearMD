"""Results' "What Next?" (feature 033): the three tools as small tiles, the one just used first,
as "<tool> Again"; the others in the start screen's order."""

from clearmd.frontend.presenter.models import NextChoice
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import Catalog


def next_choices(catalog: Catalog, current: Tool) -> tuple[NextChoice, ...]:
    others = [tool for tool in Tool if tool is not current]
    choices = []
    for tool in (current, *others):
        name = catalog.text(f"gui.more.{tool.value}")
        title = catalog.text("gui.more.again", tool=name) if tool is current else name
        choices.append(NextChoice(tool, title, tool is current))
    return tuple(choices)
