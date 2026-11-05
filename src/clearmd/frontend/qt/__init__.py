"""The PySide6 GUI (feature 016, ADR-0038): the same presenter as the ttk window, drawn by Qt.

Needs the ``qt`` extra (``pip install clearmd[qt]``)."""

from clearmd.frontend.qt.app import QtApp, main

__all__ = ["QtApp", "main"]
