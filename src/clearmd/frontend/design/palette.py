"""ClearMD's colours (ADR-0027), shared by every GUI: the ttk and PySide6 windows draw from the
same two palettes. Plain data: no toolkit is imported here."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    mode: str  # "light" or "dark"
    rail: str
    rail_text: str
    rail_muted: str
    rail_hover: str
    ground: str  # the working area behind the cards
    card: str
    text: str
    muted: str
    border: str
    accent: str  # the primary action, the current step
    accent_hover: str
    accent_text: str  # the accent as text on the ground (the step counter)
    on_accent: str
    clear: str  # the light accent: the "Clear" tone
    shape: str  # the background shape
    warning: str
    danger: str
    success: str

    @property
    def theme(self) -> str:
        return f"clearmd-{self.mode}"


LIGHT = Palette(
    mode="light",
    rail="#1B2733",
    rail_text="#F3F5F7",
    rail_muted="#A9B4BE",
    rail_hover="#26333F",
    ground="#F3F5F7",
    card="#FFFFFF",
    text="#1B2733",
    muted="#5B6672",
    border="#DCE2E7",
    accent="#0F766E",
    accent_hover="#0B5A54",
    accent_text="#0F766E",
    on_accent="#FFFFFF",
    clear="#0D9488",
    shape="#D7EEEA",
    warning="#B45309",
    danger="#B91C1C",
    success="#15803D",
)
DARK = Palette(
    mode="dark",
    rail="#0F161C",
    rail_text="#E6EBEF",
    rail_muted="#93A0AB",
    rail_hover="#1A242D",
    ground="#18212A",
    card="#202B36",
    text="#E6EBEF",
    muted="#A3AEB8",
    border="#2E3B47",
    accent="#2DD4BF",
    accent_hover="#5EEAD4",
    accent_text="#5EEAD4",
    on_accent="#0B1F1C",
    clear="#99F6E4",
    shape="#1E3A3A",
    warning="#F59E0B",
    danger="#F87171",
    success="#4ADE80",
)
PALETTES = {"light": LIGHT, "dark": DARK}
