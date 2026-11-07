"""What the rail draws on its canvas (ADR-0027, ADR-0029): ground, logo, Home, steps and foot.

The canvas keeps the state; these functions receive what they draw from (``Scene``) and a ``keep``
callable that holds each picture, because Tk forgets an image Python does not hold.
"""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import ttk
from typing import Literal

from PIL import ImageTk

from clearmd.frontend.design.colors import blend
from clearmd.frontend.design.metrics import COMPACT_RAIL_WIDTH, GAP, HALF, RADIUS, RAIL_WIDTH, SPACE
from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.visuals import marks, shapes, tool_marks

_STEP_HEIGHT = 44
_TOP = 3 * SPACE  # the logo's distance from the rail's top edge
STEPS_TOP = 12 * SPACE  # where the first step starts
_BADGE = 24  # a step's circle
_DIM = 0.55  # how strong the steps not on screen are drawn (ADR-0029)
_OFF = 0.3  # and Home while the work runs: it cannot be opened (feature 023)
_HOUSE = 14  # Home's mark, in its circle

Keep = Callable[[object], ImageTk.PhotoImage]


@dataclass(frozen=True)
class Scene:
    """What the rail shows: the fonts, the step on screen, the compact mode, the texts."""

    fonts: dict[str, tkfont.Font]
    page: int
    compact: bool
    labels: list[str]
    local: str
    version: str
    home: str = ""  # Home's word (feature 023), above the steps
    home_enabled: bool = True


def draw_rail(
    canvas: tk.Canvas,
    keep: Keep,
    p: Palette,
    scene: Scene,
    height: int,
    buttons: tuple[ttk.Button, ttk.Button],
) -> None:
    """The whole rail, from the ground to the foot; ``buttons`` are Settings and Help."""
    left, top = GAP, GAP
    width = COMPACT_RAIL_WIDTH if scene.compact else RAIL_WIDTH
    bottom = height - GAP
    ground = shapes.rounded(width, bottom - top, 2 * RADIUS, p.rail)
    canvas.create_image(left, top, image=keep(ground), anchor="nw")

    x = left + (width - 40) // 2 if scene.compact else left + GAP
    logo = keep(marks.logo("clearmd-mark-dark-40"))
    canvas.create_image(x, top + _TOP, image=logo, anchor="nw")
    if not scene.compact:
        mark_middle = top + _TOP + 20
        text_x = x + 40 + SPACE
        wordmark = scene.fonts["wordmark"]
        for part, colour in (("Clear", p.rail_text), ("·", p.clear), ("MD", p.rail_text)):
            canvas.create_text(
                text_x, mark_middle, text=part, fill=colour, font=wordmark, anchor="w"
            )
            text_x += wordmark.measure(part)

    y = top + STEPS_TOP
    draw_step(canvas, keep, scene, p, 0, scene.home, left, y, width)  # Home (feature 023)
    y += _STEP_HEIGHT + HALF
    for index, label in enumerate(scene.labels, start=1):
        draw_step(canvas, keep, scene, p, index, label, left, y, width)
        y += _STEP_HEIGHT + HALF

    draw_foot(canvas, scene, p, left, bottom, width, buttons)


def draw_step(
    canvas: tk.Canvas,
    keep: Keep,
    scene: Scene,
    p: Palette,
    index: int,
    label: str,
    left: int,
    y: int,
    width: int,
) -> None:
    """One step: its highlight or click target, its numbered circle and its word. Step 0 is Home:
    a house in its circle, fainter while it cannot be opened."""
    on_screen = index == scene.page
    tag = f"step{index}"
    if on_screen:
        highlight = shapes.rounded(width - GAP, _STEP_HEIGHT, RADIUS - 2, p.accent)
        canvas.create_image(left + SPACE, y, image=keep(highlight), anchor="nw", tags=tag)
    else:  # a target for the click, the size of the step
        canvas.create_rectangle(
            left + SPACE, y, left + width - SPACE, y + _STEP_HEIGHT,
            fill=p.rail, outline="", tags=tag,
        )  # fmt: skip
    reachable = index != 0 or scene.home_enabled
    strength = _DIM if reachable else _OFF
    colour = p.on_accent if on_screen else blend(p.rail_text, p.rail, strength)
    middle = y + _STEP_HEIGHT // 2
    badge_x = left + width // 2 if scene.compact else left + GAP + SPACE + _BADGE // 2
    circle = shapes.circle(_BADGE, outline=colour, fill=p.accent if on_screen else p.rail)
    canvas.create_image(badge_x, middle, image=keep(circle), tags=tag)
    if index == 0:
        house = keep(tool_marks.house(colour, _HOUSE))
        canvas.create_image(badge_x, middle, image=house, tags=tag)
    else:
        canvas.create_text(
            badge_x, middle, text=str(index), fill=colour, font=scene.fonts["strong"], tags=tag
        )
    if not scene.compact:
        canvas.create_text(
            badge_x + _BADGE // 2 + SPACE + HALF, middle, text=label, fill=colour,
            font=scene.fonts["strong" if on_screen else "body"], anchor="w", tags=tag,
        )  # fmt: skip


def draw_foot(
    canvas: tk.Canvas,
    scene: Scene,
    p: Palette,
    left: int,
    bottom: int,
    width: int,
    buttons: tuple[ttk.Button, ttk.Button],
) -> None:
    """The foot: the local line and the version, then Help and Settings above them."""
    settings, help_button = buttons
    x = left + GAP
    foot = bottom - GAP
    body = scene.fonts["body"]
    line = body.metrics("linespace")
    if scene.compact:
        canvas.create_text(
            left + width // 2, foot, text=scene.version, fill=p.rail_muted, font=body,
            anchor="s",
        )  # fmt: skip
        texts_height = line
    else:
        local = f"{scene.local}\n{scene.version}" if scene.version else scene.local
        canvas.create_text(
            x, foot, text=local, fill=p.rail_muted, font=body, anchor="sw",
            width=width - 2 * GAP,
        )  # fmt: skip
        lines = max(1, body.measure(scene.local) // (width - 2 * GAP) + 1)
        texts_height = (lines + (1 if scene.version else 0)) * line
    buttons_bottom = foot - texts_height - SPACE
    # As wide as the steps' band, their height (feature 011); centred marks when compact.
    anchor_x = left + width // 2 if scene.compact else left + SPACE
    anchor: Literal["s", "sw"] = "s" if scene.compact else "sw"
    band = width - GAP
    places = (
        (help_button, buttons_bottom),
        (settings, buttons_bottom - _STEP_HEIGHT - HALF),
    )
    for button, bottom_y in places:
        canvas.create_window(
            anchor_x, bottom_y, window=button, anchor=anchor, width=band, height=_STEP_HEIGHT
        )
