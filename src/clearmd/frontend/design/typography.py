"""Text sizes in pixels, the same for every GUI (UX §5: never below 14 px). Each toolkit turns
them into its own units (Tk: negative numbers). A module of its own: both GUIs read it."""

BODY = 14
SMALL = 14  # never below the body size
TITLE = 24
SUBTITLE = 16
STRONG = 14  # body size, bold: buttons, headings
EYEBROW = 14  # the step counter, bold
WORDMARK = 20  # Clear·MD on the rail
FIGURE = 24  # a summary's figure
