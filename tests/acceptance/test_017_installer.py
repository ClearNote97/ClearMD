"""Feature 017 — the Windows installer (spec/features/017_windows-installer/spec.md): what the
repository can check. The install, the use and the uninstall run on Windows in CI
(packaging/check_installer.ps1); here: that the script, the workflow and the packaging say what
the criteria promise."""

import re
from pathlib import Path

from support.inno import edition

ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "packaging" / "installer" / "clearmd.iss"
CHECK = ROOT / "packaging" / "check_installer.ps1"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"
PACKAGE = ROOT / "packaging" / "package.sh"


def read(path: Path) -> str:
    # utf-8-sig: the files carry a byte order mark (Inno Setup and PowerShell need it).
    return path.read_text(encoding="utf-8-sig")


def sections(text: str) -> dict[str, list[str]]:
    """The entries of each [Section] of the script (comments and blank lines dropped)."""
    found: dict[str, list[str]] = {}
    current = ""
    for line in text.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"\[[A-Za-z]+\]", stripped):
            current = stripped[1:-1]
            found.setdefault(current, [])
        elif current and stripped and not stripped.startswith((";", "#")):
            found[current].append(stripped)
    return found


def test_ac_01_the_release_builds_the_installer_after_the_signed_executables() -> None:
    release = read(RELEASE)
    assert "name: Installer (compiled from dist/" in release
    assert "packaging/installer/clearmd.iss" in release and "/DAppVersion=" in release
    assert "packaging/notices.py > dist/installer/THIRD-PARTY-NOTICES.txt" in release
    check_executables = release.index("packaging/check_executables.sh dist")
    assert check_executables < release.index("name: Installer (compiled from dist/")
    assert release.index("name: Installer (compiled from dist/") < release.index(
        "      - name: Package\n"
    )
    package = read(PACKAGE)
    assert 'cp "${lights[0]}" "${fulls[0]}" release/' in package  # two editions since 037
    assert "ClearMD-Setup-[0-9]*.exe" in package and "expected one ClearMD-Setup" in package
    release = read(RELEASE)
    assert "choco install innosetup --version=6.7.1 -y --no-progress" in release
    assert "Inno Setup compiler:" in release and "ProductVersion" in release
    assert "uses: " not in release.split("name: Inno Setup 6")[1].split("      - name:")[0]


def test_ac_02_per_user_only_in_the_local_programs_folder() -> None:
    setup = sections(edition(read(ISS)))["Setup"]
    assert "PrivilegesRequired=lowest" in setup
    assert "DefaultDirName={localappdata}\\Programs\\ClearMD" in setup
    assert "DisableProgramGroupPage=yes" in setup
    assert "LicenseFile={#Root}\\LICENSE" in setup
    assert "UninstallDisplayIcon={app}\\clearmd.ico" in setup
    assert "SetupIconFile={#Root}\\src\\clearmd\\frontend\\assets\\logo\\clearmd.ico" in setup
    files = sections(edition(read(ISS)))["Files"]
    assert any("dist\\ClearMD-Classic\\*" in f and "Components: ttk" in f for f in files)
    assert any(
        "dist\\ClearMD-Qt\\*" in f and "recursesubdirs" in f and "Components: qt" in f
        for f in files
    )
    assert any("dist\\clearmd-cli.exe" in f and "Components: cli" in f for f in files)
    assert any("THIRD-PARTY-NOTICES.txt" in f and '"{app}"' in f for f in files)
    assert any("LICENSE" in f and "ClearMD-Qt" in f for f in files)
    script = sections(edition(read(ISS)))
    components = script["Components"]
    assert [c.split(";")[0].split('"')[1] for c in components] == ["ttk", "qt", "flet", "cli"]
    types = script["Types"]
    assert types[0].startswith('Name: "ttkonly"'), "the classic app is the default type"
    assert [t.split('"')[1] for t in types] == [
        "ttkonly",
        "qtonly",
        "fletonly",
        "clionly",
        "full",
        "custom",
    ]
    assert any("Flags: iscustom" in t for t in types)


def test_ac_03_every_program_file_and_shortcut_belongs_to_a_component() -> None:
    script = sections(edition(read(ISS)))
    always = ("clearmd.ico", "LICENSE", "THIRD-PARTY-NOTICES.txt")
    for entry in script["Files"]:
        if not any(name in entry for name in always):
            assert "Components:" in entry, entry
    for entry in script["Icons"]:
        if "{uninstallexe}" not in entry:
            assert "Components:" in entry, entry
    assert any("{cmd}" in e and "Components: cli" in e for e in script["Icons"])


def test_ac_03_the_desktop_task_is_unticked_and_the_path_task_is_for_the_command_line() -> None:
    tasks = sections(edition(read(ISS)))["Tasks"]
    desktop = next(t for t in tasks if t.startswith('Name: "desktopicon"'))
    assert "Flags: unchecked" in desktop
    path = next(t for t in tasks if t.startswith('Name: "addpath"'))
    assert "Components: cli" in path and "Flags: unchecked" in path
    icons = "\n".join(sections(edition(read(ISS)))["Icons"])
    assert '"{group}\\{cm:ShortcutCli}"' in icons
    assert 'Filename: "{cmd}"' in icons and "--help" in icons
    assert 'Filename: "{app}\\clearmd-cli.exe"' not in icons  # never started directly


def test_ac_03_the_wizard_speaks_english_and_spanish_and_explains_each_part() -> None:
    script = edition(read(ISS))
    languages = sections(script)["Languages"]
    assert any("Default.isl" in x for x in languages)
    assert any("Languages\\Spanish.isl" in x for x in languages)
    for key in (
        "CompareTtk",
        "CompareQt",
        "CompareFlet",
        "CompareCli",
        "CompareAll",
        "NeedOneComponent",
        "RemoveSettings",
    ):
        for lang in ("english", "spanish"):
            assert re.search(rf"^{lang}\.{key}=", script, re.MULTILINE), f"{lang}.{key}"
    assert (
        "lightest" in script and "liviana" in script
    )  # the classic app is recommended, said plainly
    assert "CustomMessage('CompareTtk')" in script and "ComparePage" in script


def test_ac_03_at_least_one_component_must_be_chosen() -> None:
    script = edition(read(ISS))
    assert "procedure InitializeWizard" in script
    assert "if CurPageID = wpSelectComponents then" in script
    needle = "WizardIsComponentSelected('ttk') or WizardIsComponentSelected('qt')"
    assert (
        needle + " or WizardIsComponentSelected('flet') or WizardIsComponentSelected('cli')"
        in script
    )
    assert "CustomMessage('NeedOneComponent')" in script


def test_ac_03_a_re_install_removes_the_parts_no_longer_chosen() -> None:
    script = sections(edition(read(ISS)))
    deletes = script["InstallDelete"]
    assert any("{app}\\ClearMD-Qt" in d and "Check: NotQt" in d for d in deletes)
    assert any("clearmd-cli.exe" in d and "Check: NotCli" in d for d in deletes)
    assert any("{group}\\ClearMD.lnk" in d and "Check: NotTtk" in d for d in deletes)
    code = edition(read(ISS))
    assert (
        "not WizardIsComponentSelected('cli')" in code
        and "not WizardIsComponentSelected('ttk')" in code
    )


def test_ac_04_the_app_id_is_fixed_and_running_apps_are_closed_first() -> None:
    setup = sections(edition(read(ISS)))["Setup"]
    assert re.search(
        r"^AppId=\{\{[0-9A-F]{8}-(?:[0-9A-F]{4}-){3}[0-9A-F]{12}\}$", "\n".join(setup), re.M
    )
    assert "CloseApplications=yes" in setup and "RestartApplications=no" in setup
    assert "CloseApplicationsFilter=*.exe" in setup


def test_ac_05_the_settings_folder_is_deleted_only_on_consent() -> None:
    code = edition(read(ISS))
    assert "ExpandConstant('{localappdata}\\ClearMD')" in code
    assert "MB_YESNO or MB_DEFBUTTON2" in code  # the default answer is No
    assert "Pos('/REMOVESETTINGS', Uppercase(GetCmdTail)) > 0" in code
    assert "UninstallSilent" in code and "DelTree(Folder, True, True, True)" in code
    assert code.count("DelTree(") == 1  # the one folder, and nothing else
    code = edition(read(ISS))
    assert "RemoveOwnPathEntry;   // before the files go" in code
    assert "RegQueryStringValue(HKEY_CURRENT_USER, MarkerKey, MarkerValue, Marker)" in code
    assert "RegDeleteValue(HKEY_CURRENT_USER, MarkerKey, MarkerValue)" in code
    assert "if SameFolder(List.Strings[I], Marker) then List.Delete(I)" in code


def test_ac_06_the_check_installs_uses_uninstalls_and_looks_for_leftovers() -> None:
    check = read(CHECK)
    for needle in (
        "/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER",
        "'/COMPONENTS=ttk,qt,flet,cli', '/TASKS=addpath'",
        "'/COMPONENTS=qt'",
        "'/REMOVESETTINGS'",
        "'--smoke'",
        "clearmd-cli.exe",
        "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
        "DisplayVersion",
        "unins000.exe",
        "kept",
        "exit 1",
    ):
        assert needle in check, needle
    assert "Get-Content -Raw -Encoding utf8" in check  # the AppId is read from the script itself
    assert "packaging/check_installer.ps1" in read(RELEASE)


def test_ac_04_an_older_build_is_installed_and_replaced_in_ci() -> None:
    release = read(RELEASE)
    assert '"/DAppVersion=0.0.1"' in release and "dist/installer-old" in release
    assert "-OldInstaller" in release and "-OldVersion" in release
    check = read(CHECK)
    assert "function Assert-Upgrade" in check and "Assert-Upgrade\n" in check
    assert (
        "exactly one Installed apps entry" in check
        and "one uninstaller in the install folder" in check
    )
