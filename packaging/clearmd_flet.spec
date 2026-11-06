# PyInstaller spec: ClearMD-Flet, the flet GUI as a folder (feature 018, ADR-0042).
#
#   uv run --no-default-groups --group build python packaging/fetch_flet_client.py
#   uv run --group build pyinstaller packaging/clearmd_flet.spec --noconfirm
#
# A folder, not one file: flet's window program (Flutter, fetched and checked beforehand) travels
# in it, in ``flet-client/flet/`` next to ``ClearMD-Flet(.exe)``, so nothing is downloaded or
# unpacked on the user's machine; a folder also starts fast. It holds only the flet window: the
# ttk and Qt windows and their toolkits stay out (the other specs leave flet out, the same way).
# ruff: noqa -- PyInstaller runs this file with its own globals (Analysis, EXE, COLLECT...).

import sys
import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

ROOT = Path(SPECPATH).parent  # noqa: F821 -- given by PyInstaller
ASSETS = ROOT / "src" / "clearmd" / "frontend" / "assets" / "logo"
WINDOWS = sys.platform == "win32"

datas = collect_data_files("clearmd", excludes=["**/README.md"])
for package in ("markitdown", "trafilatura", "justext", "courlan", "htmldate"):
    datas += collect_data_files(package)
# importlib.metadata: ClearMD's version (in its summaries) and markitdown's plugin lookup.
for distribution in ("clearmd", "markitdown"):
    datas += copy_metadata(distribution)

# The light executable's rules (feature 010, ADR-0032): the same as packaging/clearmd.spec.
HEAVY = ["magika", "onnxruntime", "numpy", "pandas"]
BABEL_KEPT = ("root.dat", "en.dat", "es.dat")


def light(datas):
    def kept(entry) -> bool:
        target = entry[0].replace("\\", "/")
        if "babel/locale-data/" not in target:
            return True
        return target.rsplit("/", 1)[-1] in BABEL_KEPT
    return [entry for entry in datas if kept(entry)]

# The product name and version inside the Windows executable (feature 006b, ADR-0037).
sys.path.insert(0, str(ROOT / "packaging"))
from version_info import version_text  # noqa: E402

VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
FILENAME = "ClearMD-Flet.exe"


def version_file() -> str | None:
    if not WINDOWS:
        return None
    path = Path(workpath) / f"version-{FILENAME}.txt"  # noqa: F821 -- given by PyInstaller
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(version_text(VERSION, FILENAME), encoding="utf-8")
    return str(path)


# Every ClearMD module, the flet window's included (the worker imports its converters by name),
# and every flet module (flet finds some of its controls by name). The other windows stay out.
OTHER_GUIS = ("clearmd.frontend.ttk", "clearmd.frontend.pyside")
OTHER_TOOLKITS = ["tkinter", "_tkinter", "ttkbootstrap", "tkinterdnd2", "PySide6", "shiboken6"]
# flet's parts for other uses: its test harness (numpy, scikit-image), its web server, its CLI.
FLET_LEFT_OUT = ("flet.testing", "flet.fastapi", "flet.pytest_plugin", "flet.cli", "flet.security")
hidden = [
    module for module in collect_submodules("clearmd") if not module.startswith(OTHER_GUIS)
] + collect_submodules("flet", filter=lambda name: not name.startswith(FLET_LEFT_OUT))
hidden += collect_submodules("flet_desktop")
datas += collect_data_files("flet") + copy_metadata("flet") + copy_metadata("flet-desktop")

# flet's window program, unpacked by packaging/fetch_flet_client.py.
CLIENT = ROOT / "build" / "flet-client" / "flet"
if not CLIENT.is_dir():
    raise SystemExit(f"{CLIENT} is missing: run packaging/fetch_flet_client.py first")

a = Analysis(  # noqa: F821
    [str(ROOT / "packaging" / "launch_flet.py")],
    pathex=[str(ROOT / "src")],
    datas=datas,
    hiddenimports=hidden,
    excludes=["pytest", "mypy", "ruff", *HEAVY, *OTHER_TOOLKITS],
    runtime_hooks=[str(ROOT / "packaging" / "no_magika.py")],
    noarchive=False,
)
a.datas = light(a.datas)

exe = EXE(  # noqa: F821
    PYZ(a.pure),  # noqa: F821
    a.scripts,
    [],
    exclude_binaries=True,
    name="ClearMD-Flet",
    console=False,
    icon=str(ASSETS / "clearmd.ico"),
    version=version_file(),
    upx=False,
)
coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    upx=False,
    name="ClearMD-Flet",
)

# The window program next to the executable, as it was unpacked: its links and its executable
# bits kept (PyInstaller's data files would lose them on Linux).
import shutil  # noqa: E402

shutil.copytree(
    CLIENT, Path(DISTPATH) / "ClearMD-Flet" / "flet-client" / "flet", symlinks=True  # noqa: F821
)
