"""The Qt window's rhythm: the same as the ttk window's (UX §5, ADR-0027), in pixels."""

SPACE = 8  # the grid: every margin, padding and gap is a multiple of it
HALF = 4  # only for tight inline pairs (an icon and its label)
GAP = 2 * SPACE  # between groups; also the one gutter around the rail and the page (014)

BODY = 14  # px: never below it (UX §5)
TITLE = 24
FIGURE = 24  # a summary's figure
WORDMARK = 20

MIN_WIDTH, MIN_HEIGHT = 800, 624
START_WIDTH, START_HEIGHT = 1080, 720
COMPACT_BELOW = 1000  # a narrower window gets the compact rail (feature 007)
SHORT_BELOW = 700  # a shorter one: Choose's add buttons side by side (review of 011)

RADIUS = 12  # cards and buttons
RAIL_WIDTH, COMPACT_RAIL_WIDTH = 216, 72
BUTTON_HEIGHT = 44  # a comfortable target (UX §5)
STEP_HEIGHT = 44
BADGE = 24  # a step's number, in its circle
ICON = 16  # a list row's file icon


def on_grid(value: int) -> bool:
    """Whether a margin or gap belongs to the grid (multiples of 8; 4 for tight pairs)."""
    return value % SPACE == 0 or value == HALF
