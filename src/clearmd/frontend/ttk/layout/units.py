"""The ttk window's own units (UX §5): Tk font sizes are negative numbers of pixels; the start
size is a geometry string. The rhythm itself is shared: ``frontend.design``. A module of its own:
the fonts, the styles and the widgets all read these numbers, so none of them can hold them."""

from clearmd.frontend.design import metrics, typography

BODY = -typography.BODY
SMALL = -typography.SMALL  # never below the body size (UX §5: minimum 14 px)
TITLE = -typography.TITLE
SUBTITLE = -typography.SUBTITLE
STRONG = -typography.STRONG  # body size, bold: buttons, headings
EYEBROW = -typography.EYEBROW  # the step counter, bold
WORDMARK = -typography.WORDMARK  # Clear·MD on the rail

START_SIZE = f"{metrics.START_WIDTH}x{metrics.START_HEIGHT}"
REDRAW_MS = 80  # backgrounds are drawn again once a resize settles (AC-09)
