"""One colour laid over another, as a plain colour: a dimmed text, a faded card. A module of its
own: every GUI's drawing reads it, and the formula must be one (the ttk window's, ADR-0027)."""


def blend(colour: str, ground: str, strength: float) -> str:
    """``colour`` drawn at ``strength`` (0..1) over ``ground``: a dimmed text, as a plain colour."""
    top, bottom = _channels(colour), _channels(ground)
    mixed = (round(t * strength + b * (1 - strength)) for t, b in zip(top, bottom, strict=True))
    return "#" + "".join(f"{value:02X}" for value in mixed)


def _channels(colour: str) -> tuple[int, int, int]:
    value = colour.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
