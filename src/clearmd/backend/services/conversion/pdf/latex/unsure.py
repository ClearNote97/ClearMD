"""The one exception every stage raises; it stands alone because symbols and nodes both need it."""


class Unsure(Exception):
    """A piece no rule places: the equation is not rewritten."""
