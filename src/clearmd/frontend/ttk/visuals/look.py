"""Installs ClearMD's styles in the theme in use, once per theme, and keeps their images."""

import tkinter as tk
from typing import Any

import ttkbootstrap as tb
from PIL import ImageTk

from clearmd.frontend.design.palette import Palette
from clearmd.frontend.ttk.visuals import styles


class Look:
    """Installs ClearMD's styles in the theme in use, once per theme, and keeps their images."""

    def __init__(self, style: tb.Style, root: tk.Misc, fonts: dict[str, Any]) -> None:
        self._style = style
        self._root = root
        self._fonts = fonts
        self._images: dict[str, list[ImageTk.PhotoImage]] = {}

    def use(self, palette: Palette) -> None:
        self._style.theme_use(palette.theme)
        if palette.theme not in self._images:
            self._images[palette.theme] = []
            styles.install(self._style, self._image, self._fonts, palette)

    def _image(self, palette: Palette, picture: Any) -> ImageTk.PhotoImage:
        image = ImageTk.PhotoImage(picture, master=self._root)
        self._images[palette.theme].append(image)  # Tk forgets an image Python does not hold
        return image
