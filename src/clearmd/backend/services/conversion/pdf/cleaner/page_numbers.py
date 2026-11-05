"""A page number alone on a line: arabic, or roman as a front matter has (008)."""

import re

# A page number, alone on the first or last line: "7", "- 7 -", "Page 7 of 20", "xii".
_PAGE_NUMBER = re.compile(
    r"[-–—|·\s]*(?:(?:page|p[áa]g(?:ina)?\.?|p\.)\s*)?(\d{1,4}|[ivxlcdm]{1,7})"
    r"(?:\s*(?:/|of|de)\s*\d{1,4})?[-–—|·\s]*",
    re.IGNORECASE,
)
_ROMAN = re.compile(r"m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})")
_ROMAN_VALUES = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}


def _roman(text: str) -> int | None:
    lowered = text.lower()
    if not lowered or not _ROMAN.fullmatch(lowered):
        return None
    total = 0
    for index, char in enumerate(lowered):
        value = _ROMAN_VALUES[char]
        following = _ROMAN_VALUES[lowered[index + 1]] if index + 1 < len(lowered) else 0
        total += -value if value < following else value
    return total


def page_number(text: str) -> tuple[str, int] | None:
    """("arabic" or "roman", the number) when the line is only a page number."""
    found = _PAGE_NUMBER.fullmatch(text)
    if found is None:
        return None
    value = found.group(1)
    if value.isdigit():
        return "arabic", int(value)
    number = _roman(value)
    return ("roman", number) if number else None
