"""Feature 030 — the queue measured (spec/features/030_*/spec.md): with the real worker, light
files never wait for a heavy one (ADR-0050)."""

from pathlib import Path

from support.pdf_builder import Text, build_pdf

from clearmd.backend.api import plan_batch, run_batch
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted


def test_ac_01_light_files_finish_before_a_heavy_one_starts(workdir: Path) -> None:
    lines = [
        Text(f"Line {n} of a long report with words.", 760 - 12 * n, size=9) for n in range(60)
    ]
    (workdir / "heavy.pdf").write_bytes(build_pdf([lines] * 40))
    for n in range(4):
        (workdir / f"light{n}.txt").write_text("hello\n" * 20, "utf-8")
    events: list[tuple[str, str]] = []

    def on_event(event: BatchEvent) -> None:
        if isinstance(event, ConversionStarted):
            events.append(("start", event.item.source.name))
        elif isinstance(event, ConversionFinished):
            events.append(("end", event.outcome.item.source.name))

    run_batch(plan_batch([workdir]), overwrite=lambda item: True, on_event=on_event)
    heavy_starts = events.index(("start", "heavy.pdf"))
    for n in range(4):
        assert events.index(("end", f"light{n}.txt")) < heavy_starts


def test_ac_02_the_decision_is_recorded() -> None:
    root = Path(__file__).resolve().parents[2]
    adr = (root / "docs" / "decisions" / "0050-one-worker-cost-ordered.md").read_text("utf-8")
    assert "No second lane, no parallel workers" in adr and "15.7 s" in adr
    roadmap = (root / "spec" / "roadmap.md").read_text("utf-8")
    assert "- [x] **030" in roadmap
