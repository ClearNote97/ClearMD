"""The window's rhythm (UX §5): an 8 px grid, 14 px body text, one primary action per screen."""

SPACE = 8  # the grid: every margin, padding and gap is a multiple of it
HALF = 4  # only for tight inline pairs (an icon and its label)
GAP = 2 * SPACE  # between groups
MARGIN = 3 * SPACE  # around the window's content

# Tk font sizes: negative numbers are pixels. The family stays the system's (Segoe UI on
# Windows, San Francisco on macOS); only the sizes are ClearMD's.
BODY = -14
SMALL = -14  # never below the body size (UX §5: minimum 14 px)
TITLE = -24
SUBTITLE = -16

STRONG = -14  # body size, bold: buttons, headings
EYEBROW = -14  # the step counter, bold
WORDMARK = -20  # Clear·MD on the rail

MIN_WIDTH = 800
MIN_HEIGHT = 624  # the lists keep their rows with the gutter on every side (014; was 600)
COMPACT_BELOW = 1000  # a narrower window gets the compact rail (feature 007)
START_SIZE = "1080x720"

RADIUS = 12  # cards and buttons (ADR-0027)
RAIL_WIDTH = 216
COMPACT_RAIL_WIDTH = 72
REDRAW_MS = 80  # backgrounds are drawn again once a resize settles (AC-09)


def on_grid(value: int) -> bool:
    """Whether a padding or gap belongs to the grid (multiples of 8; 4 for tight pairs)."""
    return value % SPACE == 0 or value == HALF


# One gutter everywhere (feature 014): the window's edge to the rail, the rail to the page's
# card, the card to the window's edges, and the page inside its card, on every side.
GUTTER = GAP
INSET = GUTTER
SHORT_BELOW = 700  # px of window height: Choose's add buttons go side by side (review of 011)
