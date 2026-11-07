"""Feature 022 — the files a public project carries, and the checksums of every release.

What the repository can check: the files exist and say what the criteria promise, and the Release
workflow writes and publishes ``SHA256SUMS.txt``. That the release really carries it is seen on
GitHub when a tag is published."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / ".github" / "ISSUE_TEMPLATE"
RELEASE = ROOT / ".github" / "workflows" / "release.yml"
PRIVATE_REPORT = "https://github.com/ClearNote97/ClearMD/security/advisories/new"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_ac_01_security_policy_reports_privately_and_checks_downloads() -> None:
    text = read(ROOT / "SECURITY.md")
    assert "## Supported versions" in text and "latest release" in text
    assert PRIVATE_REPORT in text and "do not open a public issue" in text
    assert "SHA256SUMS.txt" in text
    assert "sha256sum --check" in text and "Get-FileHash" in text  # Linux and Windows


def test_ac_02_contributing_explains_the_process_and_links_the_rules() -> None:
    text = read(ROOT / "CONTRIBUTING.md")
    for check in ("ruff check .", "ruff format --check .", "mypy --strict src tests", "pytest -q"):
        assert check in text
    assert "acceptance criteria" in text and "test_ac_NN" in text
    for link in ("./CODE_OF_CONDUCT.md", "./SECURITY.md", "./LICENSE"):
        assert f"]({link})" in text and (ROOT / link).is_file()


def test_ac_03_code_of_conduct_adopts_the_covenant_and_says_how_to_report() -> None:
    text = read(ROOT / "CODE_OF_CONDUCT.md")
    assert "Contributor Covenant, version 2.1" in text
    assert "## Enforcement" in text and PRIVATE_REPORT in text


def test_ac_04_issues_open_from_two_forms_and_security_goes_private() -> None:
    forms = sorted(path.name for path in TEMPLATES.glob("*.yml") if path.name != "config.yml")
    assert forms == ["bug_report.yml", "feature_request.yml"]
    for form in forms:
        text = read(TEMPLATES / form)
        assert re.search(r"^name: .+$", text, re.M) and "body:" in text
        assert "required: true" in text
    config = read(TEMPLATES / "config.yml")
    assert "blank_issues_enabled: false" in config and PRIVATE_REPORT in config


def test_ac_05_changelog_points_to_the_notes_and_the_citation_has_the_version() -> None:
    changelog = read(ROOT / "CHANGELOG.md")
    assert "](./packaging/RELEASE_NOTES.md)" in changelog
    project = tomllib.loads(read(ROOT / "pyproject.toml"))["project"]
    citation = read(ROOT / "CITATION.cff")
    assert citation.startswith("cff-version: 1.2.0")
    assert f'\nversion: "{project["version"]}"\n' in citation
    assert "license: MIT" in citation


def test_ac_06_every_release_publishes_its_checksums_and_says_how_to_use_them() -> None:
    workflow = read(RELEASE)
    publish = workflow[workflow.index("  publish:") :]
    # Written outside the folder, so the list does not hash itself, then moved in with the files.
    assert "(cd release && sha256sum -- * > ../SHA256SUMS.txt)" in publish
    assert "mv SHA256SUMS.txt release/" in publish
    assert publish.index("SHA256SUMS.txt") < publish.index(
        'gh release create "$GITHUB_REF_NAME" release/*'
    )
    for doc in ("packaging/RELEASE_NOTES.md", "README.md", "README.es.md"):
        text = read(ROOT / doc)
        assert "SHA256SUMS.txt" in text and "SECURITY.md#checking-a-download" in text
