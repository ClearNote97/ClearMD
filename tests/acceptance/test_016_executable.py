"""Feature 016 — AC-09, the executable: what the repository can check (spec/features/016_*/spec.md).

The folder ``ClearMD-Qt/`` is built, started and measured by the workflows (CI on Windows and
Linux: packaging/check_executables.sh). Here: that the spec, the checks, the packaging and the
release say what AC-09 promises, and that the Qt trimming rules keep what the window needs.
"""

import ast
import re
import runpy
import tomllib
from importlib.metadata import distribution
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging"
PYSIDE_SPEC = PACKAGING / "clearmd_pyside.spec"
TTK_SPEC = PACKAGING / "clearmd.spec"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_ac_09_the_qt_program_is_a_folder_with_its_own_spec() -> None:
    spec = read(PYSIDE_SPEC)
    assert 'name="ClearMD-Qt"' in spec and "exclude_binaries=True" in spec
    assert "COLLECT(" in spec and "console=False" in spec
    assert "launch_pyside.py" in spec and "clearmd.ico" in spec
    assert "version=version_file()" in spec and 'FILENAME = "ClearMD-Qt.exe"' in spec
    launcher = read(PACKAGING / "launch_pyside.py")
    assert "from clearmd.frontend.pyside import main" in launcher
    assert "sys.exit(main())" in launcher
    assert 'clearmd-pyside = "clearmd.frontend.pyside:main"' in read(ROOT / "pyproject.toml")


def test_ac_09_the_qt_program_leaves_the_other_toolkits_out() -> None:
    spec = read(PYSIDE_SPEC)
    assert 'OTHER_GUIS = ("clearmd.frontend.ttk", "clearmd.frontend.flet")' in spec
    for toolkit in ("tkinter", "_tkinter", "ttkbootstrap", "tkinterdnd2", "flet"):
        assert f'"{toolkit}"' in spec, toolkit
    assert 'HEAVY = ["magika", "onnxruntime", "numpy", "pandas"]' in spec
    assert '"pytest", "mypy", "ruff", *HEAVY, *OTHER_TOOLKITS' in spec
    assert 'BABEL_KEPT = ("root.dat", "en.dat", "es.dat")' in spec
    assert "no_magika.py" in spec


def _is_qt_rule(node: ast.stmt) -> bool:
    if isinstance(node, ast.FunctionDef):
        return node.name == "qt_kept"
    if isinstance(node, ast.Assign):
        return any(
            isinstance(target, ast.Name) and target.id == "QT_LEFT_OUT" for target in node.targets
        )
    return False


def _qt_rules() -> dict[str, Any]:
    """The Qt spec's trimming rules, read from the spec itself (not copied into the test)."""
    tree = ast.parse(read(PYSIDE_SPEC))
    wanted: list[ast.stmt] = [node for node in tree.body if _is_qt_rule(node)]
    namespace: dict[str, Any] = {}
    exec(compile(ast.Module(body=wanted, type_ignores=[]), str(PYSIDE_SPEC), "exec"), namespace)
    return namespace


def test_ac_09_the_qt_trim_keeps_what_the_window_draws_with() -> None:
    qt_kept = _qt_rules()["qt_kept"]
    kept = [
        "PySide6/Qt/lib/libQt6Core.so.6",
        "PySide6/Qt/lib/libQt6Gui.so.6",
        "PySide6/Qt/lib/libQt6Widgets.so.6",
        "PySide6/Qt/lib/libQt6Svg.so.6",  # the window's pictures are SVG
        "PySide6/Qt/plugins/platforms/libqxcb.so",
        "PySide6/Qt/plugins/platforms/libqoffscreen.so",
        "PySide6/Qt/plugins/platforms/qwindows.dll",
        "PySide6/Qt/plugins/imageformats/libqsvg.so",
        "PySide6/Qt/translations/qt_es.qm",
        "PySide6/QtGui.abi3.so",
    ]
    for entry in kept:
        assert qt_kept((entry, "", "BINARY")), entry


def test_ac_09_the_qt_trim_leaves_out_what_clearmd_never_uses() -> None:
    qt_kept = _qt_rules()["qt_kept"]
    left_out = [
        "PySide6/Qt/lib/libQt6Network.so.6",
        "PySide6/Qt/plugins/tls/libqopensslbackend.so",
        "PySide6/Qt/plugins/networkinformation/libqglib.so",
        "PySide6/Qt/plugins/platforms/libqvnc.so",
        "PySide6/Qt/plugins/platforms/libqeglfs.so",
        "PySide6/Qt/plugins/egldeviceintegrations/libqeglfs-x11-integration.so",
        "PySide6/Qt/lib/libQt6EglFsKmsSupport.so.6",
        "PySide6/Qt/plugins/generic/qtuiotouchplugin.dll",
        "PySide6/Qt/translations/qt_de.qm",
        "PySide6/Qt/translations/qtbase_fr.qm",
        "PySide6/QtNetwork.abi3.so",
        "PySide6/Qt6Network.dll",
    ]
    for entry in left_out:
        assert not qt_kept((entry, "", "BINARY")), entry


def test_ac_09_the_ttk_program_and_the_cli_still_carry_no_qt() -> None:
    spec = read(TTK_SPEC)
    assert 'name="ClearMD"' in spec and 'name="clearmd-cli"' in spec
    assert '"PySide6"' in spec and '"shiboken6"' in spec and "*OTHER_TOOLKITS" in spec
    assert "not module.startswith(OTHER_GUIS)" in spec
    assert "COLLECT(" not in spec and "exclude_binaries" not in spec
    assert "clearmd.frontend.pyside" in spec  # the ttk spec leaves the Qt window out


def test_ac_09_the_check_starts_the_qt_window_and_caps_its_folder() -> None:
    check = read(PACKAGING / "check_executables.sh")
    assert 'qt_dir="$dist/ClearMD-Qt"' in check
    assert 'xvfb-run -a "$qt" --smoke' in check and '"$qt" --smoke' in check
    cap = re.search(r"^QT_MAX_MB=(\d+)$", check, re.MULTILINE)
    assert cap is not None and 150 <= int(cap.group(1)) <= 400
    assert "MAX_MB=50" in check  # the single-file programs keep their own cap
    assert "pyi-archive_viewer" in check and "could not be listed" in check
    assert "tkinter|_tkinter|ttkbootstrap|tkinterdnd2|flet" in check


def test_ac_09_the_packaging_zips_the_folder_and_puts_it_in_the_linux_archive() -> None:
    package = read(PACKAGING / "package.sh")
    assert 'release/ClearMD-Qt-$version-windows.zip" ClearMD-Qt' in package
    assert "python -m zipfile -c" in package and "--group build" in package
    assert 'cp -a "$dist/ClearMD-Qt" "stage/ClearMD-$version-linux/"' in package
    assert 'version="${version//\\//-}"' in package


def test_ac_09_the_release_builds_both_specs_and_signs_the_qt_exe() -> None:
    release = read(ROOT / ".github" / "workflows" / "release.yml")
    assert "packaging/clearmd.spec --noconfirm" in release
    assert "packaging/clearmd_pyside.spec --noconfirm" in release
    assert release.count("dist/ClearMD-Qt/ClearMD-Qt.exe") == 3  # upload, signature, product
    assert "libegl1" in release and "libxcb-cursor0" in release and "libdbus-1-3" in release
    assert "name: Sign them (SignPath)" in release
    assert "release/*" in release and "packaging/check_executables.sh dist" in release


def test_ac_09_the_notices_list_pyside_and_say_the_qt_libraries_are_replaceable() -> None:
    notices = runpy.run_path(str(PACKAGING / "notices.py"))
    describe = notices["describe"]
    essentials: str = describe(distribution("pyside6-essentials"))
    assert essentials.startswith("PySide6_Essentials") and "LGPL-3.0-only" in essentials
    shiboken: str = describe(distribution("shiboken6"))
    assert shiboken.startswith("shiboken6 ")
    note = notices["QT_NOTE"]
    assert "LGPL-3.0" in note and "replace them" in note and "ClearMD-Qt/" in note


def test_ac_09_the_version_resource_names_the_qt_exe() -> None:
    version_info = runpy.run_path(str(PACKAGING / "version_info.py"))
    text = version_info["version_text"](
        tomllib.loads(read(ROOT / "pyproject.toml"))["project"]["version"], "ClearMD-Qt.exe"
    )
    assert "StringStruct('ProductName', 'ClearMD')" in text
    assert "StringStruct('OriginalFilename', 'ClearMD-Qt.exe')" in text
    assert "StringStruct('InternalName', 'ClearMD-Qt')" in text
