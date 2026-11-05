"""Terminal prompts: whether anyone can answer, and the decision about existing outputs."""

import sys
from collections.abc import Callable
from typing import TextIO

from clearmd.backend.schemas.models import BatchPlan, PlannedConversion
from clearmd.frontend.cli.report import p
from clearmd.i18n import Catalog

PROMPT_ATTEMPTS = 3

Decision = Callable[[PlannedConversion], bool]


# --- Terminal I/O (replaceable in the tests) ---------------------------------------------------


def is_interactive() -> bool:
    return sys.stdin.isatty()


def ask(prompt: str) -> str | None:
    """One answer from the user, or ``None`` at the end of input."""
    print(prompt, end="", file=sys.stderr, flush=True)
    line = sys.stdin.readline()
    return line.strip() if line else None


# --- Decisions about existing outputs (AC-14 - AC-16) -----------------------------------------


def ask_once(catalog: Catalog, plan: BatchPlan) -> Decision:
    """One question for the whole batch; any doubt means the safe answer: keep them."""
    prompt = catalog.text("cli.ask_existing", count=len(plan.existing))
    for _ in range(PROMPT_ATTEMPTS):
        answer = ask(prompt)
        if answer is None:
            break
        if answer == "1":
            return lambda item: True
        if answer == "2":
            return lambda item: False
        if answer == "3":
            yes = catalog.text("cli.yes_letter").casefold()
            chosen = set()
            for item in plan.existing:
                target = item.target.relative_to(item.output_root.parent)
                reply = ask(catalog.text("cli.ask_one", target=p(target)))
                if reply is not None and reply.casefold().startswith(yes):
                    chosen.add(item.target)
            return lambda item: item.target in chosen
    return lambda item: False


def decision(
    catalog: Catalog, plan: BatchPlan, on_existing: str, stream: TextIO
) -> Decision | None:
    """``None`` when a decision is required but nobody can answer (exit 3, AC-18)."""
    if on_existing == "overwrite":
        return lambda item: True
    if on_existing == "skip" or not plan.existing:
        return lambda item: False
    if not is_interactive():
        print(catalog.text("cli.decision_required", count=len(plan.existing)), file=stream)
        return None
    return ask_once(catalog, plan)
