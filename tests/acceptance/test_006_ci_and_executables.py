"""Feature 006 — the criteria the repository can check (spec/features/006_*/spec.md).

What only CI can run (the builds, the checks of the executables, the release) is the workflows'
own job; here: that they say what the spec promises, and that the pieces they use exist.
"""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
PACKAGING = ROOT / "packaging"


def workflow(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def test_ac_01_ci_runs_every_check_on_linux_and_windows_with_pinned_actions() -> None:
    ci = workflow("ci.yml")
    for command in ("ruff check", "ruff format --check", "mypy", "pytest", "uv sync --locked"):
        assert command in ci
    assert re.search(r"os: \[ubuntu-[\d.]+, windows-\d+\]", ci)
    assert 'python: ["3.12", "3.14"]' in ci
    assert "permissions:\n  contents: read" in ci
    for text in (ci, workflow("release.yml")):
        uses = re.findall(r"uses: (\S+)", text)
        assert uses and all(re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", use) for use in uses)


def test_ac_02_two_one_file_programs_per_system() -> None:
    spec = (PACKAGING / "clearmd.spec").read_text(encoding="utf-8")
    assert 'name="ClearMD"' in spec and 'name="clearmd"' in spec
    assert "console=False" in spec and "console=True" in spec
    assert "Splash(" in spec and "clearmd.ico" in spec
    release = workflow("release.yml")
    assert "windows-" in release and "ubuntu-" in release
    assets = ROOT / "src" / "clearmd" / "frontend" / "assets" / "logo"
    assert (assets / "clearmd.ico").is_file() and (assets / "splash.png").is_file()


def test_ac_03_each_build_is_checked_by_a_real_batch_and_the_window() -> None:
    check = (PACKAGING / "check_executables.sh").read_text(encoding="utf-8")
    assert "--smoke" in check and "Resumen_ClearMD.md" in check
    looped = re.search(r"for name in (.*?); do", check, re.DOTALL)
    assert looped is not None
    names = looped.group(1).replace("\\", " ").split()
    names += re.findall(r"fixtures/\w+/([\w.]+)\"", check)
    assert {"sample.pdf", "docx_without_extension", "paper.tex", "report.odt"} <= set(names)
    for name in names:
        assert list(ROOT.glob(f"tests/fixtures/*/{name}")), name
    assert "packaging/check_executables.sh" in workflow("release.yml")


def test_ac_04_a_tag_publishes_a_prerelease_with_the_notices() -> None:
    release = workflow("release.yml")
    assert 'tags: ["v*"]' in release and "workflow_dispatch" in release
    assert "startsWith(github.ref, 'refs/tags/v')" in release
    assert "--prerelease" in release and "contents: write" in release
    package = (PACKAGING / "package.sh").read_text(encoding="utf-8")
    assert "THIRD-PARTY-NOTICES.txt" in package and "notices.py" in package


def test_ac_05_the_release_notes_explain_the_warning_in_both_languages() -> None:
    notes = (PACKAGING / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert (
        "More info → Run anyway" in notes and "Más información → Ejecutar de todas formas" in notes
    )
    assert "never uses the internet" in notes and "nunca usa internet" in notes


def test_ac_06_pyinstaller_is_a_pinned_build_only_dependency() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert not any("pyinstaller" in d.lower() for d in project["project"]["dependencies"])
    build = project["dependency-groups"]["build"]
    assert any(re.fullmatch(r"pyinstaller==[\d.]+", d) for d in build)
