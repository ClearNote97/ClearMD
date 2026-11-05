"""What the equation finder needs of a line; alone, so every finder module can type on it."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Placed:
    """What the equation finder needs of a line: its text and where it stands."""

    text: str
    top: float
    bottom: float
    size: float
    right: float
    other: bool  # a table, a picture, sideways text: never part of an equation
    left: float = 0.0
