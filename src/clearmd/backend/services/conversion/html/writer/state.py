"""What the writer's modules share: the limits and the tags the article subset knows.

Every limit that bounds what a page may make ClearMD write lives here (except ``MAX_CELLS``, which
the table writer owns).
"""

from typing import Any

GROWTH_FACTOR = 4
GROWTH_EXTRA = 1024**2
MAX_NESTING = 32  # quotes, tables and divisions inside each other
MAX_LIST_LEVEL = 10  # a list nested deeper is written as its text
MAX_UNKNOWN = 1000
# hi@rend → the property it sets.
HI: dict[str, dict[str, Any]] = {
    "#b": {"bold": True}, "#i": {"italic": True}, "#u": {"underline": True},
    "#t": {"mono": True}, "#sup": {"position": "super"}, "#sub": {"position": "sub"},
}  # fmt: skip
BLOCKS = frozenset({"head", "p", "list", "quote", "code", "table", "div", "ab"})
