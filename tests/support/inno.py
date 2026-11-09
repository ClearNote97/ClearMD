"""The installer script as one edition compiles it (feature 037, ADR-0052): the
``#if Edition == "..."`` blocks resolved, every other line kept (the look's #if too)."""


def edition(script: str, chosen: str = "Full") -> str:
    kept: list[str] = []
    stack: list[bool | None] = []  # True/False: an Edition block taken or not; None: any other #if
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.startswith("#if"):
            if stripped.startswith("#if Edition =="):
                stack.append(stripped.split('"')[1] == chosen)
            else:
                stack.append(None)
                kept.append(line)
            continue
        if stripped == "#else" and stack:
            if stack[-1] is None:
                kept.append(line)
            else:
                stack[-1] = not stack[-1]
            continue
        if stripped == "#endif" and stack:
            if stack.pop() is None:
                kept.append(line)
            continue
        if all(taken is not False for taken in stack):
            kept.append(line)
    return "\n".join(kept) + "\n"
