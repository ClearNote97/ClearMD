"""The names of the ttk styles ClearMD adds on top of ttkbootstrap's.

Standing alone: every view and component reads them, and ``styles`` and ``buttons`` define them.
"""

# The ttk styles ClearMD adds (on top of ttkbootstrap's).
PRIMARY = "Primary.ClearMD.TButton"  # the one primary action of a screen
SOFT = "Soft.ClearMD.TButton"  # a secondary action: white, a thin border
SOFT_ON_CARD = "SoftOnCard.ClearMD.TButton"  # the same, inside a card
STRONG = "Strong.ClearMD.TButton"  # a second action that matters as much (Convert more)
RAIL = "Rail.ClearMD.TButton"  # Settings and Help on the dark rail
RAIL_COMPACT = "RailCompact.ClearMD.TButton"  # their marks alone, centred (compact rail)
RAIL_TEXT_X = 40  # with the face's own inner border (12 px): a step's word's start (rail.py)
LINK = "Link.ClearMD.TButton"  # a quiet action on the ground
CARD = "Card.ClearMD.TFrame"  # a white, rounded card
PAGE = "Page.ClearMD.TFrame"  # the working area's ground
MUTED = "Muted.ClearMD.TLabel"  # secondary text on a card
# A card shown before there is anything to show in it: faded, like the rail's steps out of reach
# (feature 014).
DIM_CARD = "Dim.Card.ClearMD.TFrame"
# A list's card while the list has the keyboard's focus: an accent ring (feature 040, F2-01).
FOCUS_CARD = "Focus.Card.ClearMD.TFrame"
DIM = "Dim.ClearMD.TLabel"  # its text
WARNING = "Warning.ClearMD.TLabel"  # a message on the ground
ON_PAGE = "OnPage.ClearMD.TLabel"  # text on the ground
HINT = "Hint.ClearMD.TLabel"  # why an action is disabled, on the ground
CHECK_ON_PAGE = "OnPage.ClearMD.TCheckbutton"  # a check box on the ground
