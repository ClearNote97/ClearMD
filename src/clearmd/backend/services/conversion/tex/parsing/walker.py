"""The tolerant walker: nodes out, and the first error it recovered from."""

from dataclasses import dataclass
from typing import Any

from pylatexenc import latexwalker
from pylatexenc.macrospec import LatexContextDb


class Unparseable(Exception):
    """pylatexenc itself failed (not a LaTeX error it can recover from)."""


class _Walker(latexwalker.LatexWalker):  # type: ignore[misc]
    """A tolerant walker that keeps the first error it recovered from."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.first_error: latexwalker.LatexWalkerParseError | None = None

    def _report_ignore_parse_error(self, exc: Any) -> None:
        if self.first_error is None:
            self.first_error = exc


@dataclass(frozen=True)
class ParseError:
    position: int
    message: str


def parse(text: str, context: LatexContextDb) -> tuple[list[Any], ParseError | None]:
    """The nodes of ``text`` and the first error recovered from; ``Unparseable`` otherwise."""
    walker = _Walker(text, latex_context=context, tolerant_parsing=True)
    try:
        nodes, _, _ = walker.get_latex_nodes()
    except (RecursionError, IndexError, ValueError, latexwalker.LatexWalkerError) as error:
        raise Unparseable(type(error).__name__) from error
    found = walker.first_error
    if found is None:
        return list(nodes), None
    message = str(getattr(found, "msg", None) or found).splitlines()[0]
    return list(nodes), ParseError(int(getattr(found, "pos", 0) or 0), message)
