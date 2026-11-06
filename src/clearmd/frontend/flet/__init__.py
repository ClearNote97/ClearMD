"""The flet GUI (feature 018, ADR-0042): the same presenter as the ttk and Qt windows, drawn by
flet (Flutter).

Needs the ``flet`` extra (``pip install clearmd[flet]``)."""

from clearmd.frontend.flet.app import main
from clearmd.frontend.flet.window.window import FletApp

__all__ = ["FletApp", "main"]
