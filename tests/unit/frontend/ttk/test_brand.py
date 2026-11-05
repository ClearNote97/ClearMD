"""ClearMD's palettes keep every text readable (ADR-0027, UX §5: WCAG AA, 4.5:1), in both themes."""

import pytest

from clearmd.frontend.design.palette import PALETTES, Palette


def luminance(colour: str) -> float:
    def channel(value: int) -> float:
        c = value / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (int(colour.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a: str, b: str) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


# (text, on what): every pair the window draws.
PAIRS = (
    ("text", "ground"),
    ("text", "card"),
    ("muted", "card"),
    ("muted", "ground"),
    ("accent_text", "ground"),
    ("accent_text", "card"),
    ("on_accent", "accent"),
    ("warning", "card"),
    ("warning", "ground"),
    ("danger", "card"),
    ("rail_text", "rail"),
    ("rail_muted", "rail"),
    ("text", "shape"),  # a selected row
    ("muted", "shape"),
    ("accent_text", "shape"),  # the Strong button (Convert more)
)


@pytest.mark.parametrize("palette", PALETTES.values(), ids=lambda p: p.mode)
@pytest.mark.parametrize(("text", "ground"), PAIRS)
def test_every_text_pair_passes_wcag_aa(palette: Palette, text: str, ground: str) -> None:
    ratio = contrast(getattr(palette, text), getattr(palette, ground))
    assert ratio >= 4.5, f"{palette.mode}: {text} on {ground} is {ratio:.2f}:1"
