"""The window's rhythm (UX §5, ADR-0027) in pixels, the same for every GUI: an 8 px grid, the
window's sizes, the radii and the rail's widths."""

SPACE = 8  # the grid: every margin, padding and gap is a multiple of it
HALF = 4  # only for tight inline pairs (an icon and its label)
GAP = 2 * SPACE  # between groups
MARGIN = 3 * SPACE  # around a dialog's content

# One gutter everywhere (feature 014): the window's edge to the rail, the rail to the page's
# card, the card to the window's edges, and the page inside its card, on every side.
GUTTER = GAP
INSET = GUTTER

MIN_WIDTH = 800
MIN_HEIGHT = 624  # the lists keep their rows with the gutter on every side (014; was 600)
START_WIDTH, START_HEIGHT = 1080, 720
COMPACT_BELOW = 1000  # a narrower window gets the compact rail (feature 007)
SHORT_BELOW = 700  # a shorter one: Choose's add buttons side by side (review of 011)

RADIUS = 12  # cards and buttons (ADR-0027)
RAIL_WIDTH = 216
COMPACT_RAIL_WIDTH = 72
BUTTON_HEIGHT = 44  # a comfortable target (UX §5)


def on_grid(value: int) -> bool:
    """Whether a padding or gap belongs to the grid (multiples of 8; 4 for tight pairs)."""
    return value % SPACE == 0 or value == HALF
