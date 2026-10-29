# PyInstaller spec: ClearMD's executables (feature 006, ADR-0028).
#
#   uv run --group build pyinstaller packaging/clearmd.spec --noconfirm
#
# Two one-file programs: ClearMD (the desktop app, no console, a splash while it unpacks) and
# clearmd-cli (the command line; not "clearmd": Windows names ignore case, it would replace the app). They share ClearMD's data: the catalogs, the logo and icons, and the
# data files of the libraries that read the documents.
# ruff: noqa -- PyInstaller runs this file with its own globals (Analysis, EXE, Splash...).

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

ROOT = Path(SPECPATH).parent  # noqa: F821 -- given by PyInstaller
ASSETS = ROOT / "src" / "clearmd" / "frontend" / "assets" / "logo"
WINDOWS = sys.platform == "win32"

datas = collect_data_files("clearmd", excludes=["**/README.md"])
for package in ("magika", "markitdown", "trafilatura", "justext", "courlan", "htmldate"):
    datas += collect_data_files(package)
# importlib.metadata: ClearMD's version (in its summaries) and markitdown's plugin lookup.
for distribution in ("clearmd", "markitdown", "magika"):
    datas += copy_metadata(distribution)

# The worker builds its converters from a name (``module:function``): import everything of ClearMD.
# Pillow finds Tk through a module it imports by name (the window's images, ADR-0027).
hidden = collect_submodules("clearmd") + ["PIL._tkinter_finder"]


def analysis(script: str) -> Analysis:  # noqa: F821
    return Analysis(  # noqa: F821
        [str(ROOT / "packaging" / script)],
        pathex=[str(ROOT / "src")],
        datas=datas,
        hiddenimports=hidden,
        excludes=["pytest", "mypy", "ruff"],
        noarchive=False,
    )


gui = analysis("launch_gui.py")
gui_splash = Splash(  # noqa: F821
    str(ASSETS / "splash.png"),
    binaries=gui.binaries,
    datas=gui.datas,
    # "Loading… N %", updated by the app at each stage of its start (feature 007), in the free
    # bottom-left corner of the picture (tests/gui/make_assets.py: SPLASH_TEXT_POSITION).
    text_pos=(40, 214),
    text_size=10,
    text_color="#A9B4BE",
    text_default="Loading… 0 %",
    always_on_top=False,
)
gui_exe = EXE(  # noqa: F821
    PYZ(gui.pure),  # noqa: F821
    gui.scripts,
    gui_splash,
    gui_splash.binaries,
    gui.binaries,
    gui.datas,
    [],
    name="ClearMD",
    console=False,
    icon=str(ASSETS / "clearmd.ico"),
    upx=False,
)

cli = analysis("launch_cli.py")
cli_exe = EXE(  # noqa: F821
    PYZ(cli.pure),  # noqa: F821
    cli.scripts,
    cli.binaries,
    cli.datas,
    [],
    name="clearmd-cli",
    console=True,
    icon=str(ASSETS / "clearmd.ico"),
    upx=False,
)
