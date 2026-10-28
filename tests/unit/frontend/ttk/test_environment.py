"""The GUI's toolkit loads: Tk, drag and drop (tkdnd) and both themes (005, T01)."""

import pytest


@pytest.mark.usefixtures("display")
def test_tk_drag_and_drop_and_both_themes_load() -> None:
    import ttkbootstrap
    from tkinterdnd2 import TkinterDnD

    root = TkinterDnD.Tk()
    try:
        assert root.TkdndVersion
        style = ttkbootstrap.Style()
        for theme in ("bootstrap-light", "bootstrap-dark"):
            style.theme_use(theme)
            assert style.theme_use() == theme
    finally:
        root.destroy()
