"""Themes, language, icon and the 8 px grid of the window (005, T04)."""

import tkinter.font as tkfont

from support.ttk_unit import pump, widgets

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.design.metrics import on_grid
from clearmd.frontend.ttk import TtkApp, layout


def test_both_clearmd_themes_apply(app: TtkApp) -> None:
    app.apply_theme("dark")
    assert app.style.theme_use() == "clearmd-dark"
    assert app.rail.cget("background") == app.palette.ground == "#18212A"
    app.apply_theme("light")
    assert app.style.theme_use() == "clearmd-light"


def test_the_language_changes_every_label(app: TtkApp) -> None:
    app.presenter.go_to(1)  # the window opens on Home (feature 023)
    app.presenter.save_settings(Settings(language="es", show_welcome=False))
    pump(app, seconds=0.1)
    assert app.actions.primary.cget("text") == "Siguiente"
    assert app.main.add_folder.cget("text") == "Agregar Carpeta"
    assert app.rail.step_texts()[0] == "> Elegir"
    assert app.surface.header()["eyebrow"] == "Paso 1 de 4"
    assert app.main.drop_zone.text() == "o suelta aquí archivos y carpetas"


def test_the_window_icon_is_the_app_icon_at_every_size(app: TtkApp) -> None:
    assert [icon.width() for icon in app.icons] == [16, 32, 48, 64, 128, 256]


def test_every_gap_is_on_the_8_px_grid_and_text_is_at_least_14_px(app: TtkApp) -> None:
    off_grid = []
    for widget in widgets(app.root):
        manager = widget.winfo_manager()
        if manager not in {"pack", "grid"}:
            continue
        info = widget.pack_info() if manager == "pack" else widget.grid_info()
        for option in ("padx", "pady", "ipadx", "ipady"):
            value = info.get(option, 0)
            for part in value if isinstance(value, tuple) else str(value).split():
                if not on_grid(int(float(part))):
                    off_grid.append((str(widget), option, part))
    assert off_grid == []
    for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont"):
        assert tkfont.nametofont(name, root=app.root).cget("size") <= layout.units.BODY  # px: < 0
    assert all(font.cget("size") <= layout.units.BODY for font in app.fonts.values())
