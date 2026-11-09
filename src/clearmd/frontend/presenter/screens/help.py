"""The Help window's sections, the same in the three windows (audit 2026-11-08, F4-02): the real
flow, the three tools, what Markdown is. The buttons are named as the windows name them, and
dropping is told only when the window can take dropped files."""

from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import Catalog

SECTIONS = (
    "markdown", "how", "tools", "formats", "where", "ai", "keyboard", "privacy", "language",
)  # fmt: skip


def help_sections(catalog: Catalog, *, drops: bool) -> tuple[tuple[str, str], ...]:
    """(title, text) for each section, in order."""
    text = catalog.text
    buttons = {
        "next": text("gui.nav.next"),
        "drop": text("gui.help.how_drop") if drops else "",
        **{tool.value: catalog.for_tool(tool).text("gui.main.convert") for tool in Tool},
    }
    sections = []
    for section in SECTIONS:
        body = (
            text(f"gui.help.{section}", **buttons)
            if section == "how"
            else text(f"gui.help.{section}")
        )
        sections.append((text(f"gui.help.{section}_title"), body))
    return tuple(sections)
