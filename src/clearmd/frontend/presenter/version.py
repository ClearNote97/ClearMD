"""The installed ClearMD's version, as the window, the help and an error's details show it."""

from importlib.metadata import PackageNotFoundError, version


def app_version() -> str:
    try:
        return version("clearmd")
    except PackageNotFoundError:  # running from sources without metadata
        return "dev"
