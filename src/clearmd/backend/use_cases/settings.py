"""Parse and serialize settings.toml. A bad file never stops the app (ADR-0012, AC-33)."""

import tomllib
from dataclasses import fields, replace

from clearmd.backend.schemas.settings import CHOICES, Settings, SettingsProblem, SettingsWarning

FILE_KEY = "settings.toml"


def _valid(name: str, value: object, default: object) -> bool:
    if isinstance(default, bool):
        return isinstance(value, bool)
    return isinstance(value, str) and value in CHOICES[name]


def parse_settings(text: str) -> tuple[Settings, tuple[SettingsWarning, ...]]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return Settings(), (SettingsWarning(FILE_KEY, SettingsProblem.UNREADABLE),)
    defaults = Settings()
    known = {field.name for field in fields(Settings)}
    values: dict[str, object] = {}
    warnings: list[SettingsWarning] = []
    for key, value in data.items():
        if key not in known:
            warnings.append(SettingsWarning(key, SettingsProblem.UNKNOWN_KEY))
        elif _valid(key, value, getattr(defaults, key)):
            values[key] = value
        else:
            warnings.append(SettingsWarning(key, SettingsProblem.INVALID_VALUE))
    return replace(defaults, **values), tuple(warnings)  # type: ignore[arg-type]


def serialize_settings(settings: Settings) -> str:
    """Flat TOML, one setting per line, in the declared order (the settings window, feature 005)."""
    lines = []
    for field in fields(Settings):
        value = getattr(settings, field.name)
        shown = ("true" if value else "false") if isinstance(value, bool) else f'"{value}"'
        lines.append(f"{field.name} = {shown}")
    return "\n".join(lines) + "\n"
