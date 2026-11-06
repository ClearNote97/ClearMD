"""The flet window's own sizes: a step's height and its numbered badge, a list's columns, the
dialogs' widths. A module of its own: the rhythm itself is shared (``frontend.design``); these few
are flet's."""

from clearmd.frontend.design.metrics import SPACE

STEP_HEIGHT = 44  # a step on the rail: a comfortable target (UX §5)
BADGE = 24  # a step's number, in its circle
ICON = 16  # a list row's file icon
NUMBER_WIDTH = 5 * SPACE  # the list's "#" column
CHECK_WIDTH = 5 * SPACE  # the list's box, on a list whose selection does something
ROW_HEIGHT = 4 * SPACE + 4  # a list row, as Qt's (UX §5)
PROGRESS_HEIGHT = SPACE  # the progress bar's thickness
DIALOG_WIDTH = 560  # a dialog's width, as Qt's default
HELP_WIDTH = 720 + 64  # wide and short: it fits a 1366 × 768 screen with its taskbar
HELP_HEIGHT = 420  # the help's scrolled sections
SETTINGS_WIDTH = 720
QUESTION_WIDTH = 480  # "Convert more"
CONTROL_WIDTH = 28 * SPACE  # the settings' controls column
# flet sizes the window from its outer edge (Windows' invisible resize borders and the title bar
# included); Qt sizes the inside. Measured on Windows (CI, 2026-11-06): a 952 x 679 flet window
# showed 936 x 640 of page. Added to the shared sizes, the page is as large as Qt's.
FRAME_WIDTH, FRAME_HEIGHT = 16, 39
