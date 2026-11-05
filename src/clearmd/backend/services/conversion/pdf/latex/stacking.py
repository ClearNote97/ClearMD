"""What stands right above or below a bar, and the sizes around it (feature 015)."""

import bisect
from collections import Counter

from clearmd.backend.services.conversion.pdf.latex.nodes import Bar, Node
from clearmd.backend.services.conversion.pdf.latex.params import ROW_EMS, SCRIPT_SIZE

BAR_REACH = 0.9  # of the text's size: a numerator starts at most this far above its bar
BAR_SLACK = 0.3  # of the text's size: a numerator reaches this far past its bar's ends
STACK_GAP = 0.6  # of the text's size: pieces of a numerator this close are one numerator


def stack(
    nodes: list[Node], bars: list[Bar], bar: Bar, size: float, *, upwards: bool
) -> tuple[list[Node], list[Bar]]:
    """What stands right above (or below) a bar, within its ends: pieces and bars one on another,
    each close to the one before it, from the bar outwards."""
    slack = BAR_SLACK * size

    def within(left: float, right: float) -> bool:
        middle = (left + right) / 2
        return (
            bar.left - slack <= left
            and right <= bar.right + slack
            and bar.left <= middle <= bar.right
        )

    sign = 1.0 if upwards else -1.0
    items: list[tuple[float, float, Node | Bar]] = []  # (near edge, far edge) from the bar
    for node in nodes:
        near, far = (node.bottom, node.top) if upwards else (node.top, node.bottom)
        if within(node.left, node.right) and sign * (node.middle - bar.at) > 0:
            items.append((sign * (near - bar.at), sign * (far - bar.at), node))
    for other in bars:
        if within(other.left, other.right) and sign * (other.at - bar.at) > 0:
            items.append((sign * (other.at - bar.at), sign * (other.at - bar.at), other))
    items.sort(key=lambda item: item[0])
    # The rows beside the bar: full-size pieces outside its ends (and outside any other bar's).
    beside = sorted(
        node.axis for node in nodes
        if not within(node.left, node.right) and node.size >= SCRIPT_SIZE * size
        and not any(other.left <= node.middle_x <= other.right for other in bars)
    )  # fmt: skip
    reach = BAR_REACH * size
    taken_nodes: list[Node] = []
    taken_bars: list[Bar] = []
    for near, far, item in items:
        if near > reach:
            break
        if isinstance(item, Node) and taken_nodes and _on_a_row(item.axis, beside, size):
            break  # the row above (or below) the fraction's, not its numerator
        if isinstance(item, Bar):
            taken_bars.append(item)
        else:
            taken_nodes.append(item)
        reach = max(reach, far + STACK_GAP * size)
    return taken_nodes, taken_bars


def _on_a_row(axis: float, rows: list[float], size: float) -> bool:
    at = bisect.bisect_left(rows, axis - ROW_EMS * size)
    return at < len(rows) and rows[at] <= axis + ROW_EMS * size


def near_size(nodes: list[Node], bar: Bar) -> float:
    """The size of the text around a bar (its numerator's, mostly)."""
    near = [
        node.size for node in nodes
        if node.right >= bar.left and node.left <= bar.right
        and abs(node.middle - bar.at) <= 3 * node.size
    ]  # fmt: skip
    return Counter(round(size, 1) for size in near).most_common(1)[0][0] if near else 10.0


def axis_of(members: list[Node]) -> float:
    return Counter(round(node.axis, 1) for node in members).most_common(1)[0][0]
