"""Feature 018 — the flet window as an executable (AC-09, AC-10): what the repository can check.
The build, the start (``--smoke``) and the install run on Windows and Linux in CI; here: that the
spec, the launcher, the workflow, the packaging and the installer say what the criteria promise."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"
ISS = PACKAGING / "installer" / "clearmd.iss"
PAINTED = PACKAGING / "installer" / "look" / "painted.iss"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_ac_09_a_folder_with_flets_window_program_and_no_other_toolkit() -> None:
    spec = read(PACKAGING / "clearmd_flet.spec")
    assert 'name="ClearMD-Flet"' in spec and "COLLECT(" in spec  # a folder
    assert 'launch_flet.py"' in spec
    assert 'OTHER_GUIS = ("clearmd.frontend.ttk", "clearmd.frontend.pyside")' in spec
    for toolkit in ("tkinter", "ttkbootstrap", "PySide6", "shiboken6"):
        assert f'"{toolkit}"' in spec
    assert '"flet-client" / "flet", symlinks=True' in spec  # next to the program, links kept
    # The other executables carry no flet.
    for other in ("clearmd.spec", "clearmd_pyside.spec"):
        assert '"flet", "flet_desktop"]' in read(PACKAGING / other)


def test_ac_09_flets_window_program_is_pinned_and_never_downloaded_on_the_users_machine() -> None:
    fetch = read(PACKAGING / "fetch_flet_client.py")
    assert 'VERSION = "1.0.5"' in fetch
    assert len(re.findall(r'"[0-9a-f]{64}"', fetch)) == 2  # a SHA-256 for Windows and for Linux
    assert "hashlib.sha256" in fetch and "found != digest" in fetch
    launcher = read(PACKAGING / "launch_flet.py")
    assert 'os.environ["FLET_VIEW_PATH"] = str(folder / "flet-client" / "flet")' in launcher
    pyproject = read(ROOT / "pyproject.toml")
    assert 'flet = ["flet==1.0.5", "flet-desktop==1.0.5"]' in pyproject
    assert 'clearmd-flet = "clearmd.frontend.flet:main"' in pyproject


def test_ac_09_ci_builds_starts_and_releases_it_on_windows_and_linux() -> None:
    release = read(RELEASE)
    assert "packaging/fetch_flet_client.py" in release
    assert "pyinstaller packaging/clearmd_flet.spec --noconfirm" in release
    assert release.index("fetch_flet_client.py") < release.index("clearmd_flet.spec")
    assert "libgtk-3-0" in release  # the Linux window program draws with GTK 3
    assert release.count('"dist/ClearMD-Flet/ClearMD-Flet.exe"') == 2  # signature, version
    check = read(PACKAGING / "check_executables.sh")
    assert 'flet="$flet_dir/ClearMD-Flet$suffix"' in check and '"$flet" --smoke' in check
    assert '"$work/.flet"' in check  # nothing unpacked into the home folder
    assert "PySide6|shiboken6" in check and "FLET_MAX_MB=" in check
    package = read(PACKAGING / "package.sh")
    assert '"$here/release/ClearMD-Flet-$version-windows.zip" ClearMD-Flet' in package
    assert 'cp -a "$dist/ClearMD-Qt" "$dist/ClearMD-Flet"' in package
    notices = read(PACKAGING / "notices.py")
    assert "FLET_NOTE" in notices and "Flutter" in notices


def test_ac_10_the_installer_offers_the_flet_app_as_a_fourth_part() -> None:
    script = read(ISS)
    assert 'Name: "flet"; Description: "{cm:CompFlet}"; Types: fletonly full' in script
    assert 'Name: "fletonly"; Description: "{cm:TypeFlet}"' in script
    assert 'Source: "{#Root}\\dist\\ClearMD-Flet\\*"; DestDir: "{app}\\ClearMD-Flet"' in script
    assert '"{group}\\ClearMD (flet)"' in script
    assert 'Name: "{app}\\ClearMD-Flet"; Check: NotFlet' in script
    painted = read(PAINTED)
    assert "CustomMessage('CardFletTitle')" in painted
    check = read(PACKAGING / "check_installer.ps1")
    assert "'/COMPONENTS=ttk,qt,flet,cli'" in check and "Invoke-Smoke 'flet'" in check
    assert "flet-client\\flet\\flet.exe" in check


def test_ac_09_the_version_resource_names_the_flet_exe() -> None:
    import runpy

    version_info = runpy.run_path(str(PACKAGING / "version_info.py"))
    text = version_info["version_text"]("1.0.0", "ClearMD-Flet.exe")
    assert "StringStruct('OriginalFilename', 'ClearMD-Flet.exe')" in text
    assert "desktop app, flet" in text
