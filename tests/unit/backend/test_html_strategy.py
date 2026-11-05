"""The HTML strategy goes from the setting or the CLI to the worker and the summary (004, T02)."""

from pathlib import Path

import pytest

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId, Strategy
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import (
    BatchPlan,
    ConversionResult,
    Detection,
    DetectionMethod,
)
from clearmd.backend.services.conversion.registry import ConverterRegistry
from clearmd.backend.use_cases.planning import build_plan
from clearmd.frontend.cli import build_parser
from clearmd.i18n import load_catalog


class _ByExtension:
    def detect(self, path: Path) -> Detection | None:
        found = {".html": FormatId.HTML, ".pdf": FormatId.PDF}.get(path.suffix)
        return Detection(found, DetectionMethod.EXTENSION) if found else None


class _Named:
    def __init__(self, name: str) -> None:
        self.name = name

    def convert(self, source: Path, detection: Detection, target: Path) -> ConversionResult:
        return ConversionResult(self.name, ())


def _plan(tmp_path: Path, strategy: Strategy | None = None) -> BatchPlan:
    (tmp_path / "page.html").write_text("<p>x</p>", encoding="utf-8")
    (tmp_path / "doc.pdf").write_bytes(b"%PDF")
    if strategy is None:
        return build_plan([tmp_path], detector=_ByExtension(), limits=Limits())
    return build_plan([tmp_path], detector=_ByExtension(), limits=Limits(), html_strategy=strategy)


def test_full_is_the_default_for_every_file(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    assert {item.strategy for item in plan.conversions} == {Strategy.FULL}


def test_article_applies_to_html_only(tmp_path: Path) -> None:
    plan = _plan(tmp_path, Strategy.ARTICLE)
    by_name = {item.source.name: item.strategy for item in plan.conversions}
    assert by_name == {"page.html": Strategy.ARTICLE, "doc.pdf": Strategy.FULL}


def test_the_registry_picks_the_converter_by_format_and_strategy() -> None:
    registry = ConverterRegistry(
        {FormatId.HTML: _Named("full")},
        strategies={(FormatId.HTML, Strategy.ARTICLE): _Named("article")},
    )
    assert registry.for_format(FormatId.HTML).name == "full"  # type: ignore[attr-defined]
    chosen = registry.for_format(FormatId.HTML, Strategy.ARTICLE)
    assert chosen.name == "article"  # type: ignore[attr-defined]
    with pytest.raises(ConversionError) as raised:
        registry.for_format(FormatId.PDF, Strategy.ARTICLE)
    assert raised.value.code is ErrorCode.UNSUPPORTED_FORMAT


@pytest.mark.parametrize(
    ("argv", "expected"),
    [([], None), (["--html", "article"], "article"), (["--html", "full"], "full")],
)
def test_the_cli_flag_overrides_the_setting_for_one_run(
    argv: list[str], expected: str | None
) -> None:
    args = build_parser(load_catalog("en")).parse_args([*argv, "x.html"])
    assert args.html == expected


def test_the_summary_names_the_strategy() -> None:
    catalog = load_catalog("en")
    assert catalog.text("summary.strategy.article", format="HTML") == "HTML (Article)"
    assert load_catalog("es").text("summary.strategy.article", format="HTML") == "HTML (Artículo)"


def test_the_article_strategy_is_estimated_with_its_own_factors(tmp_path: Path) -> None:
    plan = _plan(tmp_path, Strategy.ARTICLE)
    page = next(item for item in plan.conversions if item.source.name == "page.html")
    limits = Limits()
    assert page.cost == limits.estimated_seconds(
        FormatId.HTML, page.source.stat().st_size, Strategy.ARTICLE
    )
    assert limits.weight(FormatId.HTML, Strategy.ARTICLE) > 10 * limits.weight(FormatId.HTML)
