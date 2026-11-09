"""Feature 037 — Two installers from one script (spec/features/037_*/spec.md, ADR-0052): read
on any system; the Windows CI builds and checks both (release.yml, check_installer.ps1)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "packaging" / "installer" / "clearmd.iss"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def full_only_lines(script: str) -> tuple[list[str], list[str]]:
    """The script's lines inside an ``#if Edition == "Full"`` block (its #else excluded), and the
    others."""
    inside, outside, stack = [], [], []
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.startswith("#if"):
            stack.append(stripped == '#if Edition == "Full"')
        elif stripped == "#else" and stack:
            stack[-1] = False if stack[-1] else stack[-1]
        elif stripped == "#endif" and stack:
            stack.pop()
        elif any(stack):
            inside.append(line)
        else:
            outside.append(line)
    return inside, outside


def test_ac_01_the_edition_must_be_chosen_and_names_the_file() -> None:
    script = read(ISS)
    assert "#ifndef Edition\n  #error" in script
    assert "OutputBaseFilename=ClearMD-Setup-Full-{#AppVersion}" in script
    assert "OutputBaseFilename=ClearMD-Setup-{#AppVersion}" in script
    release = read(ROOT / ".github" / "workflows" / "release.yml")
    assert '"/DEdition=Light"' in release and '"/DEdition=Full"' in release


def test_ac_02_the_light_edition_never_touches_the_other_parts() -> None:
    _inside, outside = full_only_lines(read(ISS))
    other = re.compile(r"WizardIsComponentSelected\('(qt|flet|cli)'\)|Components: (qt|flet|cli)\b")
    assert [line for line in outside if other.search(line)] == []
    assert not [line for line in outside if "Check: NotQt" in line or "Check: NotFlet" in line]
    script = read(ISS)
    guid = re.search(r"AppId=\{\{([0-9A-F-]{36})\}", script)
    assert guid and f'#define AppGuid "{guid.group(1)}"' in script
    refusal = script[script.index("function InitializeSetup") :]
    assert "Inno Setup: Selected Components" in refusal and "Result := False" in refusal
    assert "LightHasOtherParts" in refusal and "spanish.LightHasOtherParts=" in script


def test_ac_03_ci_checks_both_editions_and_the_update_from_2_8_1() -> None:
    check = read(ROOT / "packaging" / "check_installer.ps1")
    for needle in ("$LightInstaller", "-le 45", "-le 190", "L2. Over 2.8.1", "Assert-NoOldNames"):
        assert needle in check
    release = read(ROOT / ".github" / "workflows" / "release.yml")
    assert (
        'gh release download v2.8.1 -D dist/installer-old -p "ClearMD-Setup-2.8.1.exe"' in release
    )
    assert "-LightInstaller" in release and "-ReleasedInstaller" in release
    package = read(ROOT / "packaging" / "package.sh")
    assert "ClearMD-Setup-[0-9]*.exe" in package and "ClearMD-Setup-Full-*.exe" in package


def test_ac_04_people_are_told_which_file_to_download() -> None:
    notes = read(ROOT / "packaging" / "RELEASE_NOTES.md")
    assert "ClearMD-Setup-Full-" in notes.split("**New in")[0]
    for readme in ("README.md", "README.es.md"):
        assert "ClearMD-Setup-Full" in read(ROOT / readme)
