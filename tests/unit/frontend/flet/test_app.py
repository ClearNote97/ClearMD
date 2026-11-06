"""``clearmd-flet`` (feature 018): ``main`` runs flet with ClearMD's assets and builds the window
on flet's page; ``--smoke`` closes it by itself. flet's program is never started here."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

import flet as ft
import pytest
from support.flet_page_stub import StubPage

import clearmd.frontend.launch as launch
from clearmd.frontend.flet import main
from clearmd.frontend.flet.visuals.images import ASSETS

Start = Callable[[Any], Coroutine[Any, Any, None]]


def run_main(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> tuple[int, Start, str]:
    seen: list[tuple[Start, str]] = []
    monkeypatch.setattr(ft, "run", lambda start, *, assets_dir: seen.append((start, assets_dir)))
    code = main(argv)
    assert len(seen) == 1
    return code, *seen[0]


def test_main_runs_flet_with_clearmds_assets(monkeypatch: pytest.MonkeyPatch) -> None:
    code, _start, assets = run_main(monkeypatch, [])
    assert code == 0 and assets == str(ASSETS)
    assert (ASSETS / "icons" / "pdf@2x.png").is_file() and (ASSETS / "logo").is_dir()


def test_the_window_is_built_on_flets_page_and_the_smoke_run_closes_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _code, start, _assets = run_main(monkeypatch, ["--smoke"])
    stub = StubPage()
    asyncio.run(start(stub.as_page()))
    assert len(stub.added) == 1 and stub.title == "ClearMD"  # the window, on the page
    assert stub.theme is not None and stub.dark_theme is not None
    delays = [seconds for seconds, _work in stub.loop.later]
    assert launch.SMOKE_SECONDS in delays  # the smoke run's close, queued
    stub.loop.run_all()  # the welcome of a first run opens, then the smoke run closes
    assert stub.dialogs == [] and stub.window.visible
    assert stub.tasks == [stub.window.destroy]


def test_without_smoke_the_window_stays(monkeypatch: pytest.MonkeyPatch) -> None:
    _code, start, _assets = run_main(monkeypatch, [])
    stub = StubPage()
    asyncio.run(start(stub.as_page()))
    assert launch.SMOKE_SECONDS not in [seconds for seconds, _work in stub.loop.later]
