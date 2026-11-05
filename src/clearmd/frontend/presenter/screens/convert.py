"""Convert: the progress of the file being converted."""

from clearmd.frontend.presenter.models import ProgressView
from clearmd.i18n import Catalog

LONG_FILE_SECONDS = 15  # after this, the file's timer and "large files can take a few minutes"


def progress_view(
    catalog: Catalog,
    current: tuple[int, int, str, float | None, str],
    done: int,
    elapsed: float,
) -> ProgressView:
    """``current``: index, total, name, seconds left, icon; ``elapsed``: seconds on this file."""
    index, total, name, left, icon = current
    long_file = elapsed >= LONG_FILE_SECONDS
    return ProgressView(
        counter=catalog.text("gui.progress.counter", index=index, total=total),
        name=name,
        fraction=done / total if total else 0.0,
        time_left=(
            catalog.text("cli.time_left", duration=catalog.duration(left))
            if left is not None
            else None
        ),
        elapsed=catalog.clock(elapsed) if long_file else None,
        long_file=catalog.text("gui.progress.long_file") if long_file else None,
        icon=icon,
    )
