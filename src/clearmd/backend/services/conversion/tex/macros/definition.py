"""A macro the author defined: its arguments, its default, and the expansion of one use."""

import re
from dataclasses import dataclass, field

_PARAMETER = re.compile(r"#([1-9#])")


@dataclass(frozen=True)
class MacroDefinition:
    name: str
    arguments: int
    default: str | None
    body: str
    uses: tuple[int, ...] = field(init=False)  # how many times #1 … #9 appear in the body

    def __post_init__(self) -> None:
        found = _PARAMETER.findall(self.body)
        object.__setattr__(
            self, "uses", tuple(found.count(str(n)) for n in range(1, self.arguments + 1))
        )

    @property
    def argspec(self) -> str:
        if self.arguments == 0:
            return ""
        if self.default is not None:
            return "[" + "{" * (self.arguments - 1)
        return "{" * self.arguments

    def size(self, values: list[str]) -> int:
        """The length of the expansion, without building it."""
        size = len(self.body) - 2 * sum(self.uses) - self.body.count("##")
        return size + sum(len(value) * uses for value, uses in zip(values, self.uses, strict=False))

    def substitute(self, values: list[str]) -> str:
        def replace(match: re.Match[str]) -> str:
            mark = match.group(1)
            if mark == "#":
                return "#"
            index = int(mark) - 1
            return values[index] if index < min(len(values), self.arguments) else match.group(0)

        return _PARAMETER.sub(replace, self.body)


_BEGIN_OR_END = re.compile(r"\\(begin|end)\s*\{")


def opens_or_closes_an_environment(definition: MacroDefinition) -> bool:
    r"""``\newcommand{\beq}{\begin{equation}}``: only text substitution keeps the document whole."""
    found = _BEGIN_OR_END.findall(definition.body)
    return definition.arguments == 0 and found.count("begin") != found.count("end")
