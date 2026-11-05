"""The delimiters each style opens and closes with, in the order styles nest."""

from dataclasses import replace

from clearmd.backend.services.conversion.inline.pieces import TextProps

_ORDER = ("bold", "italic", "strike", "underline", "position")
_OPEN = {"bold": "**", "italic": "*", "strike": "~~", "underline": "<u>"}
_CLOSE = {"bold": "**", "italic": "*", "strike": "~~", "underline": "</u>"}


def active(props: TextProps) -> list[str]:
    found = []
    for key in _ORDER:
        value = getattr(props, key)
        if value:
            found.append(f"position:{value}" if key == "position" else key)
    return found


_POSITION_TAG = {"super": "sup", "sub": "sub"}


def opener(key: str) -> str:
    if key.startswith("position:"):
        return f"<{_POSITION_TAG[key.split(':')[1]]}>"
    return _OPEN[key]


def closer(key: str) -> str:
    if key.startswith("position:"):
        return f"</{_POSITION_TAG[key.split(':')[1]]}>"
    return _CLOSE[key]


EMPHASIS = ("bold", "italic", "strike")


def without(props: TextProps, keys: set[str]) -> TextProps:
    return replace(
        props,
        bold=props.bold and "bold" not in keys,
        italic=props.italic and "italic" not in keys,
        strike=props.strike and "strike" not in keys,
    )
