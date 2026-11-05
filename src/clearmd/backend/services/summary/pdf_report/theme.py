"""The page and its look: measures, the app's light palette (ADR-0027), and the ``Run`` of text."""

from dataclasses import dataclass

from clearmd.backend.services.summary.model import Mark

REGULAR, BOLD = b"Helvetica", b"Helvetica-Bold"
WIDTH, HEIGHT = 595.0, 842.0  # A4, in points
MARGIN = 48.0
BAND = 76.0  # the teal band at the top of the first page
NOTE_ITEMS = 20
MAX_SHOWN = 200  # characters of a name, folder or result; their middle goes past it
MAX_DETAIL = 500  # characters of a technical detail
CELL_SIZE = 8.5
HEADING_ROOM = 44 + 18  # a heading never alone at a page's foot: one line of what follows too
TABLE_SHARES = (0.22, 0.17, 0.20, 0.31, 0.10)  # document, folder, result, format, time

Colour = tuple[int, int, int]


def rgb(value: str) -> Colour:
    """A ``#RRGGBB`` colour as three bytes."""
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


# The app's light palette (ADR-0027): a printed page is light.
TEXT, MUTED, BORDER = rgb("#1B2733"), rgb("#5B6672"), rgb("#DCE2E7")
ACCENT, SHAPE, WHITE = rgb("#0F766E"), rgb("#D7EEEA"), rgb("#FFFFFF")
MARK_COLOURS: dict[Mark, Colour] = {
    Mark.DONE: rgb("#15803D"),
    Mark.ATTENTION: rgb("#B45309"),
    Mark.FAILED: rgb("#B91C1C"),
    Mark.STOPPED: rgb("#5B6672"),
}
LEFT_OUT = rgb("#A9B4BE")  # a file that was not tried: a quiet grey dot


@dataclass(frozen=True)
class Run:
    """A piece of text in one style."""

    text: str
    bold: bool = False
    colour: Colour = TEXT
