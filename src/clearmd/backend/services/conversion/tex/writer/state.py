"""What the writer shares between its modules: the types of the callbacks it is given."""

from collections.abc import Callable

# The link target for an image argument, or ``None`` when it must not become a link (ADR-0022).
ImageHandler = Callable[[str], str | None]
