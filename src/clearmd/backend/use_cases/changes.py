"""Whether an original changed since its result was written (feature 028, ADR-0048): the
original is newer than its result. A split file's result is its parts' folder."""

import os

from clearmd.backend.schemas.models import PlannedConversion


def changed_since_result(item: PlannedConversion) -> bool:
    """True when the original was modified after its result (or its parts' folder) was
    written; also when either cannot be read, so that the safe answer is a fresh result."""
    try:
        return os.stat(item.source).st_mtime > os.stat(item.target).st_mtime
    except OSError:
        return True
