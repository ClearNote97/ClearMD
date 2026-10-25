"""The real clock (the use cases receive it through the ``Clock`` port)."""

from datetime import datetime


class SystemClock:
    def now(self) -> datetime:
        return datetime.now().astimezone()
