"""ClearMD's look in Qt (ADR-0027, ADR-0038): one style sheet written from the shared palette.

Widgets are named (``objectName``) or carry a property (``tone``, ``dim``); the sheet gives each its
colours, radius and padding. Nothing here depends on a widget: changing the theme is one call.
"""

from importlib.resources import files

from clearmd.frontend.palette import Palette
from clearmd.frontend.pyside.layout import (
    BODY,
    BUTTON_HEIGHT,
    FIGURE,
    GAP,
    RADIUS,
    SPACE,
    TITLE,
    WORDMARK,
)

PICTURES = files("clearmd.frontend") / "assets" / "pyside"


def _picture(name: str, p: Palette) -> str:
    """A path the style sheet can read (forward slashes on every system)."""
    return str(PICTURES / f"{name}-{p.mode}.svg").replace("\\", "/")


DIM_STRENGTH = 0.45  # a faded card: this much of the card's colour on the ground's (as ttk, 014)
DIM_TEXT = 0.8  # its text: this much of the muted colour on the faded card


def blend(colour: str, ground: str, strength: float) -> str:
    """``colour`` laid over ``ground`` with ``strength`` (0: the ground, 1: the colour)."""
    front = [int(colour[i : i + 2], 16) for i in (1, 3, 5)]
    back = [int(ground[i : i + 2], 16) for i in (1, 3, 5)]
    mixed = (round(b + (f - b) * strength) for f, b in zip(front, back, strict=True))
    return "#" + "".join(f"{value:02X}" for value in mixed)


def stylesheet(p: Palette) -> str:
    dim_card = blend(p.card, p.ground, DIM_STRENGTH)
    dim_text = blend(p.muted, dim_card, DIM_TEXT)
    disabled = blend(p.muted, p.card, 0.5)
    rail_dim = blend(p.rail_text, p.rail, 0.55)
    return f"""
QWidget {{ font-size: {BODY}px; color: {p.text}; }}
QWidget#window, QWidget#ground {{ background: {p.ground}; }}
QDialog {{ background: {p.ground}; }}
QToolTip {{ color: {p.text}; background: {p.card}; border: 1px solid {p.border}; }}

QFrame#rail {{ background: {p.rail}; border-radius: {2 * RADIUS}px; }}
QFrame#rail QLabel {{ color: {p.rail_text}; background: transparent; }}
QFrame#rail QLabel#wordmark {{ font-size: {WORDMARK}px; font-weight: bold; }}
QFrame#rail QLabel#local {{ color: {p.rail_muted}; }}
QPushButton#step, QPushButton#railButton {{
    color: {rail_dim}; background: transparent; border: none; border-radius: {RADIUS - 2}px;
    text-align: left; padding: 0 {SPACE}px; min-height: {BUTTON_HEIGHT}px; font-weight: normal;
}}
QPushButton#railButton {{ color: {p.rail_text}; padding-left: {5 * SPACE}px; }}
QFrame#rail[compact="true"] QPushButton#step,
QFrame#rail[compact="true"] QPushButton#railButton {{ text-align: center; padding: 0; }}
QPushButton#step:hover, QPushButton#railButton:hover {{ background: {p.rail_hover}; }}
QPushButton#step[current="true"] {{
    color: {p.on_accent}; background: {p.accent}; font-weight: bold;
}}
QPushButton#step:focus, QPushButton#railButton:focus {{ border: 2px solid {p.clear}; }}
QPushButton#railButton:disabled {{ color: {rail_dim}; }}

QLabel#eyebrow {{ color: {p.accent_text}; font-weight: bold; background: transparent; }}
QLabel#title {{ font-size: {TITLE}px; font-weight: bold; background: transparent; }}
QLabel#subtitle, QLabel#hint {{ color: {p.muted}; background: transparent; }}
QLabel#message {{ color: {p.warning}; background: transparent; }}
QLabel#onPage {{ background: transparent; }}
QLabel#strong {{ font-weight: bold; background: transparent; }}
QLabel#muted {{ color: {p.muted}; background: transparent; }}
QLabel#figure {{ font-size: {FIGURE}px; font-weight: bold; background: transparent; }}
QLabel#figure[tone="accent"] {{ color: {p.accent_text}; }}
QLabel#figure[tone="warning"] {{ color: {p.warning}; }}
QLabel#figure[tone="danger"] {{ color: {p.danger}; }}
QLabel#bigText {{ font-size: {TITLE}px; font-weight: bold; background: transparent; }}

QFrame#panel {{ background: {p.ground}; border: 1px solid {p.border}; border-radius: {RADIUS}px; }}
QFrame#card {{ background: {p.card}; border: 1px solid {p.border}; border-radius: {RADIUS}px; }}
QFrame#card[dim="true"] {{ background: {dim_card}; border-color: {dim_card}; }}
QFrame#card[dim="true"] QLabel {{ color: {dim_text}; }}
QFrame#card QLabel, QFrame#card QRadioButton, QFrame#card QCheckBox {{ background: transparent; }}
QFrame#drop {{
    background: {p.card}; border: 2px dashed {p.muted}; border-radius: {RADIUS}px;
}}
QFrame#drop:hover {{ border-color: {p.accent}; }}
QFrame#drop QLabel {{ color: {p.muted}; background: transparent; }}

QPushButton {{
    background: {p.card}; color: {p.text}; border: 1px solid {p.border};
    border-radius: {RADIUS - 2}px; padding: 0 {GAP}px; min-height: {BUTTON_HEIGHT}px;
    font-weight: bold;
}}
QPushButton:hover {{ border-color: {p.accent}; }}
QPushButton:focus {{ border: 2px solid {p.accent}; }}
QPushButton:disabled {{ color: {disabled}; border-color: {p.border}; }}
QPushButton#primary {{ background: {p.accent}; color: {p.on_accent}; border: none; }}
QPushButton#primary:hover {{ background: {p.accent_hover}; }}
QPushButton#primary:focus {{ border: 2px solid {p.text}; }}
QPushButton#primary:disabled {{ background: {p.border}; color: {disabled}; }}
QPushButton#strong {{ border: 2px solid {p.accent}; color: {p.accent_text}; }}
QPushButton#link {{
    background: transparent; border: none; color: {p.accent_text}; padding: 0 {SPACE}px;
}}
QPushButton#link:hover {{ background: {blend(p.border, p.ground, 0.6)}; }}
QPushButton#link:disabled {{ color: {disabled}; }}

QRadioButton, QCheckBox {{ spacing: {SPACE}px; background: transparent; }}
QRadioButton:disabled, QCheckBox:disabled {{ color: {disabled}; }}
QRadioButton::indicator {{
    width: 14px; height: 14px; border-radius: 9px; border: 2px solid {p.muted};
    background: {p.card};
}}
QRadioButton::indicator:checked {{
    border-color: {p.accent};
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
        stop:0 {p.accent}, stop:0.5 {p.accent}, stop:0.62 {p.card}, stop:1 {p.card});
}}
QRadioButton::indicator:focus, QCheckBox::indicator:focus {{ border-color: {p.accent}; }}
QRadioButton::indicator:disabled, QCheckBox::indicator:disabled {{ border-color: {p.border}; }}
QCheckBox::indicator, QTreeWidget::indicator {{
    width: 14px; height: 14px; border-radius: 4px; border: 2px solid {p.muted};
    background: {p.card};
}}
QCheckBox::indicator:checked, QTreeWidget::indicator:checked {{
    border-color: {p.accent}; background: {p.accent}; image: url({_picture("check", p)});
}}
QComboBox {{
    background: {p.card}; border: 1px solid {p.border}; border-radius: {RADIUS - 4}px;
    padding: {SPACE // 2}px {SPACE}px; min-height: {3 * SPACE}px; min-width: {24 * SPACE}px;
}}
QComboBox:focus {{ border: 2px solid {p.accent}; }}
QComboBox::drop-down {{ border: none; width: {3 * SPACE}px; }}
QComboBox::down-arrow {{ image: url({_picture("arrow", p)}); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{
    background: {p.card}; color: {p.text}; border: 1px solid {p.border};
    selection-background-color: {p.accent}; selection-color: {p.on_accent};
}}
QScrollBar:vertical {{ background: transparent; width: {SPACE + 2}px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {p.border}; border-radius: {(SPACE + 2) // 2}px; min-height: {4 * SPACE}px;
}}
QScrollBar::handle:vertical:hover {{ background: {p.muted}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QTreeWidget {{
    background: {p.card}; border: 1px solid {p.border}; border-radius: {RADIUS}px;
    padding: {SPACE}px; alternate-background-color: {p.card};
    selection-background-color: {blend(p.accent, p.card, 0.18)}; selection-color: {p.text};
}}
QTreeWidget::item {{ min-height: {4 * SPACE + 4}px; }}
QHeaderView::section {{
    background: {p.card}; color: {p.muted}; font-weight: bold; border: none;
    border-right: 1px solid {p.border}; padding: {SPACE // 2}px {SPACE}px;
}}
QLabel#empty {{ color: {p.muted}; background: transparent; }}

QProgressBar {{
    background: {p.border}; border: none; border-radius: {SPACE // 2}px; max-height: {SPACE}px;
}}
QProgressBar::chunk {{ background: {p.accent}; border-radius: {SPACE // 2}px; }}
QScrollArea {{ background: transparent; border: none; }}
"""
