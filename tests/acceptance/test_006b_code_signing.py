"""Feature 006b — code signing (spec/features/006b_code-signing/spec.md): what the repository can
check. The signing itself runs on SignPath, from the release workflow."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / ".github" / "workflows" / "release.yml"


def steps() -> list[str]:
    """The release workflow's build steps, each as its own text, in order."""
    text = RELEASE.read_text(encoding="utf-8").split("\n  publish:")[0]
    build = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    return re.split(r"\n      - ", build.split("    steps:\n", 1)[1])


def test_ac_01_the_windows_executables_are_signed_before_they_are_checked() -> None:
    names = [step.splitlines()[0] for step in steps()]
    signing = next(i for i, n in enumerate(names) if "signpath/github-action-submit" in n.lower())
    upload = next(i for i, n in enumerate(names) if "Unsigned" in n)
    built = next(i for i, n in enumerate(names) if n == "name: Build")
    checked = next(i for i, n in enumerate(names) if n.startswith("name: Check the executables"))
    assert built < upload < signing < checked
    sign = steps()[signing]
    assert "wait-for-completion: true" in sign and "output-artifact-directory: dist" in sign
    assert "secrets.SIGNPATH_API_TOKEN" in sign and "vars.SIGNPATH_ORGANIZATION_ID" in sign


def test_ac_02_with_no_signpath_set_up_the_build_is_as_before() -> None:
    for step in steps():
        if "SIGNPATH" in step or "Unsigned" in step or "Authenticode" in step:
            assert "runner.os == 'Windows' && vars.SIGNPATH_ORGANIZATION_ID != ''" in step, step


def test_ac_03_a_signed_build_is_verified() -> None:
    verify = next(step for step in steps() if "Authenticode" in step.splitlines()[0])
    assert "Get-AuthenticodeSignature" in verify and "Valid" in verify
    assert "ClearMD.exe" in verify and "clearmd-cli.exe" in verify


def test_ac_04_the_code_signing_policy_is_published() -> None:
    policy = (ROOT / "CODE_SIGNING.md").read_text(encoding="utf-8")
    for text in (
        "Free code signing provided by [SignPath.io]",
        "certificate by [SignPath Foundation]",
        "Committers and reviewers",
        "Approvers",
        "will not transfer any information to other networked systems",
    ):
        assert text in policy, text
    for readme in ("README.md", "README.es.md"):
        assert "CODE_SIGNING.md" in (ROOT / readme).read_text(encoding="utf-8"), readme


def test_ac_05_documented() -> None:
    adr = ROOT / "docs" / "decisions" / "0037-code-signing.md"
    assert adr.exists() and "Status:** accepted" in adr.read_text(encoding="utf-8")
    assert "0037-code-signing.md" in (ROOT / "docs" / "decisions" / "README.md").read_text(
        encoding="utf-8"
    )
