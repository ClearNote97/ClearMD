"""The GUI's toolkit loads: Tk, drag and drop (tkdnd) and ClearMD's two themes (005, T01, T04b)."""

import pytest


@pytest.mark.usefixtures("display")
def test_tk_drag_and_drop_and_both_themes_load() -> None:
    import ttkbootstrap
    from tkinterdnd2 import TkinterDnD

    from clearmd.frontend.ttk.visuals.themes import register_themes

    root = TkinterDnD.Tk()
    try:
        assert root.TkdndVersion
        ttkbootstrap.Style.instance = None  # the process-wide Style may belong to a closed window
        style = ttkbootstrap.Style()
        register_themes(style)
        for theme in ("clearmd-light", "clearmd-dark"):
            style.theme_use(theme)
            assert style.theme_use() == theme
    finally:
        root.destroy()
