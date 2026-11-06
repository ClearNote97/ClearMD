# PyInstaller spec: ClearMD-Qt, the PySide6 GUI as a folder (feature 016, ADR-0038, ADR-0003).
#
#   uv run --group build pyinstaller packaging/clearmd_pyside.spec --noconfirm
#
# A folder, not one file: PySide6 is LGPL, so the user must be able to replace the Qt libraries,
# which are plain files inside ``dist/ClearMD-Qt/``. It holds only the Qt window: the ttk window,
# flet and their toolkits stay out (packaging/clearmd.spec leaves PySide6 out, the same way).
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
FILENAME = "ClearMD-Qt.exe"


def version_file() -> str | None:
    if not WINDOWS:
        return None
    path = Path(workpath) / f"version-{FILENAME}.txt"  # noqa: F821 -- given by PyInstaller
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(version_text(VERSION, FILENAME), encoding="utf-8")
    return str(path)


# Every ClearMD module, the Qt window's included (the worker imports its converters by name).
# The ttk window and flet stay out: each executable holds one GUI.
OTHER_GUIS = ("clearmd.frontend.ttk", "clearmd.frontend.flet")
OTHER_TOOLKITS = ["tkinter", "_tkinter", "ttkbootstrap", "tkinterdnd2", "flet", "flet_desktop"]
# The Qt modules ClearMD does not import: their Python bindings (the libraries go by qt_kept).
QT_MODULES_LEFT_OUT = ["PySide6.QtNetwork", "PySide6.QtDBus"]
hidden = [
    module for module in collect_submodules("clearmd") if not module.startswith(OTHER_GUIS)
]

# Qt keeps what the window draws with (Core, Gui, Widgets, Svg for its pictures, DBus for Gui,
# the desktop platforms). Left out: the network stack (ClearMD never uses it), the embedded and
# remote platforms, the touch-input plugin, and the translations other than Spanish (ClearMD
# speaks two languages). Matched in lower case on the file's place in the bundle, Windows or Linux.
QT_LEFT_OUT = (
    "qt6network", "qtnetwork.", "plugins/tls/", "networkinformation/", "qvnc", "qlinuxfb",
    "qeglfs", "qt6eglfs", "qvkkhrdisplay", "qtuiotouchplugin", "egldeviceintegrations/",
)  # fmt: skip


def qt_kept(entry) -> bool:
    target = entry[0].replace("\\", "/").lower()
    if target.endswith(".qm") and "/translations/" in target:
        return target.endswith("_es.qm")
    return not any(part in target for part in QT_LEFT_OUT)

a = Analysis(  # noqa: F821
    [str(ROOT / "packaging" / "launch_pyside.py")],
    pathex=[str(ROOT / "src")],
    datas=datas,
    hiddenimports=hidden,
    excludes=["pytest", "mypy", "ruff", *HEAVY, *OTHER_TOOLKITS, *QT_MODULES_LEFT_OUT],
    runtime_hooks=[str(ROOT / "packaging" / "no_magika.py")],
    noarchive=False,
)
a.datas = [entry for entry in light(a.datas) if qt_kept(entry)]
a.binaries = [entry for entry in a.binaries if qt_kept(entry)]

exe = EXE(  # noqa: F821
    PYZ(a.pure),  # noqa: F821
    a.scripts,
    [],
    exclude_binaries=True,
    name="ClearMD-Qt",
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
    name="ClearMD-Qt",
)
