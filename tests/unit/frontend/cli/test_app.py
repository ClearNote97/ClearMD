from importlib.metadata import version

import pytest

from clearmd.frontend.cli import main


def test_version_flag_prints_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"clearmd {version('clearmd')}"


def test_no_arguments_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage: clearmd" in capsys.readouterr().out


def test_unknown_argument_exits_with_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--no-existe"])

    assert exit_info.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err
