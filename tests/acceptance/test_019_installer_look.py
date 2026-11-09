"""Feature 019 — the installer's look (spec/features/019_installer-look/spec.md): what the
repository can check. The wizard itself is photographed on Windows by the installer-look workflow;
the release compiles and checks the installer with this look (packaging/check_installer.ps1)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "packaging" / "installer"
ISS = INSTALLER / "clearmd.iss"
BRAND = INSTALLER / "look" / "brand.iss"
PAINTED = INSTALLER / "look" / "painted.iss"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"
LOOK = ROOT / ".github" / "workflows" / "installer-look.yml"
# Connectors stay in lower case in a title (the owner's Title Case rule); the first word never does.
CONNECTORS = {
    *"a an the of for and or to in on with by".split(),
    *"de del al la el los las y o a en con por para sin un una".split(),
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_ac_01_the_painted_look_is_the_default_and_needs_inno_6_7() -> None:
    script = read(ISS)
    assert '#define Look "painted"' in script
    assert '#include "look\\brand.iss"' in script and '#include "look\\painted.iss"' in script
    assert "PaintCompareCards(ComparePage);" in script and "PaintWizard;" in script
    release = read(RELEASE)
    assert "--version=6.7.1" in release and "Inno Setup 6.7 or newer is needed" in release
    assert "packaging/installer/inno_version.ps1" in release
    assert "/DLook=" not in release  # the release builds the default


def test_ac_02_clearmd_pictures_for_every_dpi_in_light_and_dark() -> None:
    brand = read(BRAND)
    assert "WizardStyle=modern light hidebevels" in brand  # always light since v1.0.1
    assert "DisableWelcomePage=no" in brand
    for directive in ("WizardImageFile", "WizardImageFileDynamicDark", "WizardSmallImageFile"):
        line = next(x for x in brand.splitlines() if x.startswith(f"{directive}="))
        files = line.split("=", 1)[1].split(",")
        assert len(files) == 4, directive  # 100, 125, 150 and 200 % DPI
        for name in files:
            assert (INSTALLER / name.replace("\\", "/")).is_file(), name


def test_ac_03_the_palette_is_the_apps_palette() -> None:
    palette = read(ROOT / "src" / "clearmd" / "frontend" / "design" / "palette.py")
    used = set(re.findall(r"#[0-9A-F]{6}", read(BRAND) + read(PAINTED)))
    assert used and used <= set(re.findall(r'"(#[0-9A-F]{6})"', palette))


def test_ac_04_the_parts_are_cards_with_the_recommended_one_marked() -> None:
    painted = read(PAINTED)
    for part in ("Ttk", "Qt", "Flet", "Cli"):
        for field in ("Title", "Tag", "Body"):
            for language in ("english", "spanish"):
                assert f"{language}.Card{part}{field}=" in painted
    assert "english.CardTtkTag=RECOMMENDED" in painted
    assert "spanish.CardTtkTag=RECOMENDADA" in painted
    assert "CustomMessage('CardTtkTitle'), CustomMessage('CardTtkTag'), " in painted
    assert "StyleElements - [seFont]" in painted  # the letters' colour, never [seClient, seFont]


def _titles() -> list[str]:
    names = re.compile(
        r"^(?:english|spanish)\.(?:Comp(?:Ttk|Qt|Flet|Cli)|Card\w+Title|CompareCaption)="
    )
    text = read(ISS) + read(PAINTED)
    titles = [x.split("=", 1)[1] for x in text.splitlines() if names.match(x)]
    titles += [x.split("=", 1)[1] for x in text.splitlines() if x.startswith("spanish.Welcome")]
    titles += [
        x.split("=", 1)[1] for x in text.splitlines() if x.startswith("spanish.FinishedHeading")
    ]
    return titles


def test_ac_05_titles_in_title_case() -> None:
    titles = _titles()
    assert len(titles) >= 16
    # " - " starts a new part of a title (a subtitle): its first word is capitalised too.
    parts = [part for title in titles for part in title.split(" - ")]
    for title in parts:
        words = [w for w in title.split() if w and w[0].isalpha()]
        for position, word in enumerate(words):
            if word.startswith(("ClearMD", "[name]")) or word in {"ttk", "flet"}:
                continue
            if position > 0 and word.lower() in CONNECTORS:
                assert word == word.lower(), (title, word)
            else:
                assert word[0].isupper(), (title, word)


def test_ac_06_the_look_is_photographed_on_windows() -> None:
    workflow = read(LOOK)
    assert "workflow_dispatch" in workflow and "runs-on: windows-2025" in workflow
    assert 'foreach ($look in "plain", "brand", "painted")' in workflow
    assert "-Lang spanish" in workflow
    shoot = read(INSTALLER / "look" / "shoot.ps1")
    assert "AppsUseLightTheme" in shoot and "CopyFromScreen" in shoot


def test_ac_07_adr_version_notes_readme_and_photographs() -> None:
    adr = ROOT / "docs" / "decisions" / "0041-installer-look.md"
    assert "Status:** accepted" in adr.read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version = "(.+)"', pyproject, re.M)
    assert version and tuple(map(int, version.group(1).split("."))) >= (0, 13, 0)
    notes = (ROOT / "packaging" / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert "ClearMD-Setup-0.13.2.exe" in notes
    assert "look/" in read(INSTALLER / "README.md")
    photos = sorted((ROOT / "docs" / "screenshots" / "019").glob("*.png"))
    assert len(photos) >= 6
