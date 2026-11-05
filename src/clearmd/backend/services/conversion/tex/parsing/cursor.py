r"""What every argument parser reads off pylatexenc's walker: the whitespace set, the
``\verb`` window, a chars node and a recovered error.

Shared by ``verbatim_args``, ``definition_args`` and ``mask``, so it stands alone.
"""

from typing import Any

from pylatexenc import latexwalker

VERB_WINDOW = 4096  # a \verb argument is on one line; never searched farther than this
SPACE = " \t\n\r"


def report(w: Any, pos: int, message: str) -> None:
    w._report_ignore_parse_error(latexwalker.LatexWalkerParseError(s=w.s, pos=pos, msg=message))


def chars(w: Any, parsing_state: Any, start: int, end: int) -> Any:
    return w.make_node(
        latexwalker.LatexCharsNode,
        parsing_state=parsing_state,
        chars=w.s[start:end],
        pos=start,
        len=end - start,
    )
