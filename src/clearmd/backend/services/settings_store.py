"""Where settings.toml lives on each OS, and reading it (ADR-0002, ADR-0012)."""

from pathlib import Path

import platformdirs

from clearmd.backend.schemas.settings import Settings, SettingsProblem, SettingsWarning
from clearmd.backend.use_cases.settings import FILE_KEY, parse_settings

APP_NAME = "ClearMD"


def settings_path() -> Path:
    return platformdirs.user_config_path(APP_NAME, appauthor=False) / FILE_KEY


def load_settings(path: Path | None = None) -> tuple[Settings, tuple[SettingsWarning, ...]]:
    """Defaults when the file is missing; defaults and a warning when it cannot be read."""
    target = path or settings_path()
    try:
        text = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Settings(), ()
    except (OSError, UnicodeDecodeError):
        return Settings(), (SettingsWarning(FILE_KEY, SettingsProblem.UNREADABLE),)
    return parse_settings(text)
