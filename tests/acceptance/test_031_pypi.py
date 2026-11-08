"""Feature 031 — ready for PyPI (spec/features/031_*/spec.md): the metadata, PyPI's page, the
build check and the publish job, as the repository holds them."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "pypi.yml"


def project() -> dict[str, object]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))
    found: dict[str, object] = data["project"]
    return found


def test_ac_01_the_metadata_shows_the_toolkit() -> None:
    meta = project()
    assert "split and merge" in str(meta["description"]) and "100% local" in str(
        meta["description"]
    )
    classifiers = list(meta["classifiers"])  # type: ignore[call-overload]
    assert "Operating System :: Microsoft :: Windows" in classifiers
    assert "Topic :: Text Processing :: Markup :: Markdown" in classifiers
    for version in ("3.12", "3.13", "3.14"):
        assert f"Programming Language :: Python :: {version}" in classifiers
    urls = dict(meta["urls"])  # type: ignore[call-overload]
    assert set(urls) >= {"Homepage", "Source", "Issues", "Changelog"}


def test_ac_02_pypis_page_has_only_absolute_links() -> None:
    assert project()["readme"] == "packaging/pypi-readme.md"
    page = (ROOT / "packaging" / "pypi-readme.md").read_text("utf-8")
    links = re.findall(r"\]\(([^)]+)\)", page)
    assert links and all(link.startswith("https://") for link in links)
    for words in ("pipx install clearmd", "--split-words", "--merge", "clearmd[pyside]"):
        assert words in page


def test_ac_03_every_tag_builds_installs_and_runs_the_wheel() -> None:
    workflow = WORKFLOW.read_text("utf-8")
    assert 'tags: ["v*"]' in workflow and "workflow_dispatch" in workflow
    assert "uv build" in workflow
    assert "uv venv /tmp/fresh" in workflow and "/tmp/fresh/bin/clearmd --version" in workflow
    assert "test -f /tmp/ClearMD_Output/OutputMD/note.md" in workflow


def test_ac_04_publishing_is_trusted_pinned_and_off_until_turned_on() -> None:
    workflow = WORKFLOW.read_text("utf-8")
    publish = workflow[workflow.index("  publish:") :]
    assert "vars.PYPI_PUBLISH == 'true'" in publish
    assert "id-token: write" in publish and "environment: pypi" in publish
    assert re.search(r"pypa/gh-action-pypi-publish@[0-9a-f]{40} # v", publish)
    assert "password" not in publish and "secrets." not in workflow  # no token anywhere
