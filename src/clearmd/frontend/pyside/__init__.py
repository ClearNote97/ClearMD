"""The PySide6 GUI (feature 016, ADR-0038): the same presenter as the ttk window, drawn by Qt.

Needs the ``pyside`` extra (``pip install clearmd[pyside]``)."""

from clearmd.frontend.pyside.app import PySideApp, main

__all__ = ["PySideApp", "main"]
