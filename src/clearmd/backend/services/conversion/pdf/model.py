"""What PDFium's text becomes: characters, lines, pages and the document (feature 008, ADR-0030).

Plain data with no PDFium in it, so the cleaner and the pure steps (``lines``, ``blocks``) use
it without reading anything.
"""

from array import array
from collections.abc import Callable
from dataclasses import dataclass, field

SOFT_HYPHEN = "­"
UNREADABLE = "�"
UPRIGHT, CLOCKWISE, COUNTERCLOCKWISE, ASLANT = range(4)  # how a character is turned


@dataclass
class Line:
    text: str
    size: float  # the height of the text, in points: headings are taller
    bold: bool
    top: float  # page coordinates (origin at the bottom): a larger gap starts a paragraph
    bottom: float
    image: str = ""  # a picture's link in the images folder: the line is the picture (012)
    turn: int = UPRIGHT  # a line of a table set sideways is turned (013)
    equation: tuple[str, ...] = ()  # the line is a display equation, its rows as laid out (013)
    left: float = 0.0
    right: float = 0.0
    table: tuple[tuple[str, ...], ...] = ()  # the line is a table found on the page (013)
    span: tuple[int, int] = (0, 0)  # its characters on the page (start, stop)
    latex: str = ""  # an equation rebuilt as LaTeX from its pieces (015)


LETTER_HEIGHT = 792.0  # points: a page whose height PDFium cannot give


@dataclass
class Page:
    lines: list[Line] = field(default_factory=list)
    height: float = LETTER_HEIGHT


@dataclass
class Document:
    pages: list[Page]
    decoded_fonts: int = 0  # fonts read back from moved codes (the summary tells it)
    unreadable: int = 0  # characters that could not be read (shown as "�")
    cut_pages: int = 0  # pages with more characters than any page holds: their first part kept
    hidden_pages: list[int] = field(default_factory=list)  # with unseen text left out (ADR-0054)
    equation_pages: list[int] = field(default_factory=list)  # equations kept as their symbols


class Chars:
    """One page's characters, compact: a few bytes each, not a Python object each (a book of
    millions of characters must fit in the worker's memory, code review of 008)."""

    def __init__(self) -> None:
        self.codes = array("I")
        self.fonts = array("I")  # the font's number in the document (``Fonts``)
        self.sizes = array("f")
        self.bottoms = array("f")
        self.tops = array("f")
        self.lefts = array("f")
        self.rights = array("f")
        self.turns = array("B")  # upright, a quarter turn either way, or aslant
        self.font_sizes = array("f")  # the font's size, as set: a script's is smaller (014)
        self.baselines = array("f")  # where it stands: a script's is raised or lowered
        self.bold = array("B")


Boxes = Callable[[int], tuple[float, float, float, float] | None]
