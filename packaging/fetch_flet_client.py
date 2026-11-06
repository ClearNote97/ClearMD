"""Fetch flet's window program for the flet executable (feature 018, ADR-0042).

flet draws with a separate program (Flutter), which flet itself downloads on first use. ClearMD
never downloads anything on the user's machine (100% local), so CI fetches it once, here, checks
it against a pinned SHA-256 and unpacks it into ``build/flet-client/flet/``; the flet spec puts that
folder inside ``ClearMD-Flet/`` and the launcher points flet to it (``FLET_VIEW_PATH``).

    uv run --no-default-groups --group build python packaging/fetch_flet_client.py
"""

import hashlib
import shutil
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

VERSION = "1.0.5"  # the same as the flet and flet-desktop pins (pyproject.toml)
# Per system: the release file and its SHA-256 (GitHub's own digest of the asset). Linux takes the
# "light" client (no media playback; ClearMD has none) built for Ubuntu 22.04, the build runner.
CLIENTS = {
    "win32": (
        "flet-windows.zip",
        "6b5bddbcf2df8d0986dec60eab0b28c8cd8be1c0cd96cd73d5e34a3122ca867d",
    ),
    "linux": (
        "flet-linux-ubuntu22.04-light-amd64.tar.gz",
        "0d81dc4e864fbe4b7f99ddc1658e8a8adc90f405fb5a355dde63c5eb793b3c93",
    ),
}
ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "build" / "flet-client"


def main() -> int:
    name, digest = CLIENTS[sys.platform]
    url = f"https://github.com/flet-dev/flet/releases/download/v{VERSION}/{name}"
    TARGET.mkdir(parents=True, exist_ok=True)
    archive = TARGET / name
    with urllib.request.urlopen(url, timeout=120) as response:  # noqa: S310 -- a fixed https URL
        archive.write_bytes(response.read())
    found = hashlib.sha256(archive.read_bytes()).hexdigest()
    if found != digest:
        print(f"{name}: SHA-256 {found}, expected {digest}", file=sys.stderr)
        return 1
    shutil.rmtree(TARGET / "flet", ignore_errors=True)
    if name.endswith(".zip"):
        with zipfile.ZipFile(archive) as packed:
            packed.extractall(TARGET)
    else:
        with tarfile.open(archive) as packed:
            packed.extractall(TARGET, filter="data")
    program = TARGET / "flet" / ("flet.exe" if sys.platform == "win32" else "flet")
    if not program.is_file():
        print(f"{program} is missing from {name}", file=sys.stderr)
        return 1
    archive.unlink()
    print(f"flet {VERSION} window program: {program}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
