"""Text for the page: what the fonts can draw, names from the user's files, wrapping and fitting."""

from collections.abc import Iterator

from clearmd.backend.services.summary.pdf_report import metrics
from clearmd.backend.services.summary.pdf_report.theme import MAX_SHOWN, Run
from clearmd.i18n import printable


def latin(text: str) -> str:
    """What the standard fonts can draw: Windows Latin; any other character is "?"."""
    return text.encode("cp1252", errors="replace").decode("cp1252")


def displayed(text: str, limit: int = MAX_SHOWN) -> str:
    """Text from the user's files, drawn as it may be printed; a very long one with its middle
    left out (a folder 4,000 characters deep is still one line or two, security audit of 009)."""
    assert limit >= 3
    shown = " ".join(printable(text[: limit * 8]).split())  # never the whole of a huge text
    if len(shown) <= limit:
        return shown
    half = (limit - 1) // 2
    return f"{shown[:half]}…{shown[-half:]}"


def latin_runs(runs: list[Run]) -> list[Run]:
    """The runs with their text in Windows Latin."""
    return [Run(latin(run.text), run.bold, run.colour) for run in runs]


def wrap(runs: list[Run], size: float, width: float) -> Iterator[list[Run]]:
    """Words of several runs into lines no wider than ``width`` (a word too long is cut)."""
    line: list[Run] = []
    used = 0.0
    for run in latin_runs(runs):
        for index, word in enumerate(run.text.split(" ")):
            piece = word if index == 0 else " " + word
            piece_width = metrics.width(piece, size, run.bold)
            if line and used + piece_width > width:
                yield line
                line, used = [], 0.0
                piece = piece.lstrip()
                piece_width = metrics.width(piece, size, run.bold)
            while piece and piece_width > width:  # one word wider than the line
                cut = metrics.cut(piece, size, width, run.bold)
                yield [*line, Run(piece[:cut], run.bold, run.colour)]
                line, used = [], 0.0
                piece = piece[cut:]
                piece_width = metrics.width(piece, size, run.bold)
            if piece:
                line.append(Run(piece, run.bold, run.colour))
                used += piece_width
    if line:
        yield line


def fit(text: str, size: float, width: float, bold: bool = False) -> str:
    """One cell's text, cut with "…" when it does not fit."""
    if metrics.width(text, size, bold) <= width:
        return text
    room = width - metrics.width("…", size, bold)
    return text[: metrics.cut(text, size, room, bold)] + "…" if room > 0 else ""
