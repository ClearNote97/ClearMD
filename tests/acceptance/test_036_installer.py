"""Feature 036, AC-07 — the installer's first run (spec/features/036_*/spec.md): read from the
script on any system; the Windows CI runs it (packaging/check_installer.ps1)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISS = ROOT / "packaging" / "installer" / "clearmd.iss"
PAINTED = ROOT / "packaging" / "installer" / "look" / "painted.iss"
CHECK = ROOT / "packaging" / "check_installer.ps1"
OLD_NAMES = ("ClearMD (Qt)", "ClearMD (flet)", "ClearMD (command line)")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def test_ac_07_parts_are_named_by_what_a_person_notices() -> None:
    script, painted = read(ISS), read(PAINTED)
    for line in (
        "english.CompTtk=Classic App (Recommended)",
        "spanish.CompQt=App Moderna",
        "spanish.CompFlet=App Estilo Móvil",
        "english.ShortcutFlet=ClearMD Mobile-Style App",
        "spanish.ShortcutCli=ClearMD Línea de Comandos",
    ):
        assert line in script
    assert "english.CardFletTag=about 120 MB" in painted  # no toolkit names (audit v3, C-3)
    titles = re.findall(r"^(?:english|spanish)\.Card\w+Title=(.*)$", painted, re.M)
    assert titles and not any(word in t for t in titles for word in ("ttk", "Qt", "flet"))


def test_ac_07_every_old_shortcut_name_is_removed_unconditionally() -> None:
    script = read(ISS)
    for name in OLD_NAMES:
        for where in ("group", "autodesktop"):
            line = f'Type: files; Name: "{{{where}}}\\{name}.lnk"'
            assert line + "\n" in script  # no Check: — whatever the choice
    icons = script[script.index("[Icons]") : script.index("[InstallDelete]")]
    assert not any(name in icons for name in OLD_NAMES)


def test_ac_07_every_custom_message_has_both_languages() -> None:
    texts = read(ISS) + read(PAINTED)
    used = set(re.findall(r"\{cm:(\w+)", texts)) | set(
        re.findall(r"CustomMessage\('(\w+)'\)", texts)
    )
    defined = {
        lang: set(re.findall(rf"^{lang}\.(\w+)=", texts, re.M)) for lang in ("english", "spanish")
    }
    builtin = {"UninstallProgram", "Name"}  # Inno's own, and the comment's example
    assert used - builtin <= defined["english"] and used - builtin <= defined["spanish"]


def test_ac_07_a_spanish_first_install_opens_in_spanish() -> None:
    script = read(ISS)
    code = script[script.index("procedure SpeakTheWizardsLanguage") :]
    code = code[: code.index("end;\n\nprocedure CurStepChanged")]
    assert "ActiveLanguage <> 'spanish'" in code and "FileExists(FileName) then Exit" in code
    assert "'language = \"es\"'" in code
    assert "SpeakTheWizardsLanguage;" in script
    check = read(CHECK)
    assert "'/LANG=spanish'" in check and 'language = "es"' in check
