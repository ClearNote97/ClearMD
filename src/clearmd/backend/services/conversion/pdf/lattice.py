"""Tables in a PDF page, found from the rules drawn around their cells (feature 013, ADR-0034).

After Camelot's "lattice" method (Vinayak Mehta and contributors, MIT;
https://camelot-py.readthedocs.io): the horizontal and vertical rules that cross one another
make a grid, and each word goes to the cell it stands in, so a cell's text wrapped over several
lines stays one cell. Camelot finds the rules in a picture of the page with OpenCV; ClearMD reads
them from the page's own drawing (thin paths), as PDFium gives them.

Pure: rules and words in, tables out.
"""

from dataclasses import dataclass

from clearmd.backend.services.conversion.pdf.tables import Table, Word

THIN = 2.0  # points: a path this thin is a rule
MIN_RULE = 10.0  # points: shorter is a tick, not a cell's side
NEAR = 2.0  # points: rules this close are one line of the grid, and meet
MIN_LINES = 3  # of each direction: two rows and two columns (a frame alone is no table)
MAX_RULES = 2000  # a page's rules looked at (each pair is compared once)


@dataclass(frozen=True)
class Rule:
    """A thin line on the page: horizontal (``at`` is its y) or vertical (``at`` is its x)."""

    horizontal: bool
    at: float
    start: float
    end: float


def rule(left: float, bottom: float, right: float, top: float) -> Rule | None:
    """The rule a path's box draws, or None (a filled box, a dot)."""
    width, height = right - left, top - bottom
    if height <= THIN and width >= MIN_RULE:
        return Rule(True, (bottom + top) / 2, left, right)
    if width <= THIN and height >= MIN_RULE:
        return Rule(False, (left + right) / 2, bottom, top)
    return None


def find_lattices(rules: list[Rule], words: list[Word]) -> list[tuple[Table, list[Word]]]:
    """The page's ruled tables, each with the words it takes (stream tables are then found
    among the rest)."""
    found: list[tuple[Table, list[Word]]] = []
    free = list(words)
    for group in _grids(rules[:MAX_RULES]):
        table, taken = _table(group, free)
        if table is not None:
            found.append((table, taken))
            gone = {id(word) for word in taken}
            free = [word for word in free if id(word) not in gone]
    return found


def _meet(a: Rule, b: Rule) -> bool:
    if a.horizontal == b.horizontal:
        return False
    flat, upright = (a, b) if a.horizontal else (b, a)
    within_x = flat.start - NEAR <= upright.at <= flat.end + NEAR
    within_y = upright.start - NEAR <= flat.at <= upright.end + NEAR
    return within_x and within_y


def _grids(rules: list[Rule]) -> list[list[Rule]]:
    """The rules that cross one another, as groups (a union of their meetings)."""
    parent = list(range(len(rules)))

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    flats = [i for i, item in enumerate(rules) if item.horizontal]
    uprights = [i for i, item in enumerate(rules) if not item.horizontal]
    for i in flats:
        for j in uprights:
            if _meet(rules[i], rules[j]):
                parent[root(i)] = root(j)
    groups: dict[int, list[Rule]] = {}
    for index, item in enumerate(rules):
        groups.setdefault(root(index), []).append(item)
    return list(groups.values())


def _lines(values: list[float]) -> list[float]:
    """Positions merged where they are one line of the grid."""
    merged: list[float] = []
    for value in sorted(values):
        if merged and value - merged[-1] <= NEAR:
            continue
        merged.append(value)
    return merged


def _table(group: list[Rule], words: list[Word]) -> tuple[Table | None, list[Word]]:
    xs = _lines([item.at for item in group if not item.horizontal])
    ys = _lines([item.at for item in group if item.horizontal])
    if len(xs) < MIN_LINES or len(ys) < MIN_LINES:
        return None, []
    ys.reverse()  # top first
    cells: dict[tuple[int, int], list[Word]] = {}
    taken = []
    for word in words:
        x, y = (word.left + word.right) / 2, (word.bottom + word.top) / 2
        column = next((i for i in range(len(xs) - 1) if xs[i] <= x < xs[i + 1]), None)
        row = next((i for i in range(len(ys) - 1) if ys[i] >= y > ys[i + 1]), None)
        if column is not None and row is not None:
            cells.setdefault((row, column), []).append(word)
            taken.append(word)
    rows = sorted({row for row, _ in cells})
    columns = sorted({column for _, column in cells})
    if len(rows) < 2 or len(columns) < 2:
        return None, []
    grid = tuple(tuple(_text(cells.get((row, column), [])) for column in columns) for row in rows)
    return Table(top=ys[0], bottom=ys[-1], left=xs[0], right=xs[-1], rows=grid), taken


def _text(words: list[Word]) -> str:
    """A cell's words in reading order: its lines top first, each from the left."""
    lines: list[list[Word]] = []
    for word in sorted(words, key=lambda w: (-w.bottom, w.left)):
        if lines and abs(lines[-1][0].bottom - word.bottom) <= 0.35 * max(word.size, 1.0):
            lines[-1].append(word)
        else:
            lines.append([word])
    return " ".join(" ".join(w.text for w in sorted(line, key=lambda w: w.left)) for line in lines)
