"""Light or dark, as the operating system is set (UX §5), without a dependency (ADR-0026).

Windows: the registry value ``AppsUseLightTheme``; macOS: ``defaults read -g AppleInterfaceStyle``;
Linux: GNOME's ``color-scheme`` (``gsettings``), then ``GTK_THEME``. Anything unknown: light.
"""

import os
import subprocess
import sys

_TIMEOUT = 1.0  # seconds: the window never waits longer to know


def detect_system_theme() -> str:
    """``"dark"`` or ``"light"``; never raises."""
    try:
        if sys.platform == "win32":
            return _windows()
        if sys.platform == "darwin":
            return _ask(["defaults", "read", "-g", "AppleInterfaceStyle"], dark="dark")
        found = _ask(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"], "dark")
        if found == "dark":
            return found
        return "dark" if ":dark" in os.environ.get("GTK_THEME", "").lower() else "light"
    except Exception:  # noqa: BLE001 -- a missing tool, a locked registry: light
        return "light"


def _windows() -> str:
    if sys.platform != "win32":  # for the type checker: winreg exists on Windows only
        return "light"
    import winreg

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
    )
    with key:
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
    return "light" if value else "dark"


def _ask(command: list[str], dark: str) -> str:
    """``"dark"`` when ``command`` prints something containing ``dark``; ``"light"`` otherwise."""
    try:
        found = subprocess.run(
            command, capture_output=True, text=True, timeout=_TIMEOUT, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return "light"
    return "dark" if dark in found.stdout.lower() else "light"
