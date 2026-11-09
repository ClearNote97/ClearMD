"""Convert: the progress of the file being converted."""

from clearmd.frontend.presenter.models import ProgressView
from clearmd.i18n import Catalog

LONG_FILE_SECONDS = 15  # after this, the file's timer and "large files can take a few minutes"


def progress_view(
    catalog: Catalog,
    current: tuple[int, int, str, float | None, str],
    done: int,
    elapsed: float,
    pages: tuple[int, int] | None = None,
) -> ProgressView:
    """``current``: index, total, name, seconds left, icon; ``elapsed``: seconds on this file;
    ``pages``: how far it has got, when its converter tells (audit 2026-11-08, 3B)."""
    index, total, name, left, icon = current
    long_file = elapsed >= LONG_FILE_SECONDS
    line = catalog.text("gui.progress.long_file") if long_file else None
    if long_file and pages is not None:  # the file moves: say how far, not only "be patient"
        line = catalog.text(
            "gui.progress.pages", done=catalog.count(pages[0]), total=catalog.count(pages[1])
        )
    return ProgressView(
        counter=catalog.text("gui.progress.counter", index=index, total=total),
        name=name,
        fraction=_fraction(done, total, pages),
        time_left=(
            catalog.text("cli.time_left", duration=catalog.duration(left))
            if left is not None
            else None
        ),
        elapsed=catalog.clock(elapsed) if long_file else None,
        long_file=line,
        icon=icon,
    )


def _fraction(done: int, total: int, pages: tuple[int, int] | None) -> float:
    """The files done, and how far the current one has got when it tells its pages: the bar
    moves while a long PDF converts (audit v3, F3-06)."""
    if not total:
        return 0.0
    within = pages[0] / pages[1] if pages is not None and pages[1] > 0 else 0.0
    return min(1.0, (done + min(within, 1.0)) / total)
