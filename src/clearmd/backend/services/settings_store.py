"""Where settings.toml lives on each OS, reading and writing it (ADR-0002, ADR-0012, ADR-0026)."""

import os
import tempfile
from pathlib import Path

import platformdirs

from clearmd.backend.schemas.settings import Settings, SettingsProblem, SettingsWarning
from clearmd.backend.use_cases.settings import FILE_KEY, parse_settings, serialize_settings

APP_NAME = "ClearMD"


CONFIG_DIR_VARIABLE = "CLEARMD_CONFIG_DIR"  # a folder of one's own: tests, a portable copy


def settings_path() -> Path:
    """``settings.toml`` in the system's configuration folder, or in ``$CLEARMD_CONFIG_DIR``."""
    chosen = os.environ.get(CONFIG_DIR_VARIABLE)
    folder = Path(chosen) if chosen else platformdirs.user_config_path(APP_NAME, appauthor=False)
    return folder / FILE_KEY


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


def save_settings(settings: Settings, path: Path | None = None) -> None:
    """Write ``settings`` atomically: a temporary file in the same folder, then a rename, so a
    crash or a full disk never leaves a half-written file (the old one stays). Only known keys
    are written, each valid (``ValueError`` otherwise); ``OSError`` if the folder is read-only."""
    target = path or settings_path()
    text = serialize_settings(settings)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".settings-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
