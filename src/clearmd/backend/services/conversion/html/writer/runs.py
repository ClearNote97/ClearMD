"""Inline runs: the properties a ``hi``, ``del`` or ``code`` element sets on its text."""

from dataclasses import replace
from typing import Any

from clearmd.backend.services.conversion.inline import TextProps


def with_props(props: TextProps, changes: dict[str, Any]) -> TextProps:
    return replace(props, **changes)
