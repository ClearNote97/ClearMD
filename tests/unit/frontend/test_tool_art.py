"""The tools' icons as shared data (feature 032, AC-04): every shape on the grid, the SVG text the
flet window shows, and the curves flattened for Pillow."""

import xml.etree.ElementTree as ET

import pytest

from clearmd.frontend.design.tool_art import (
    ART,
    GRID,
    Circle,
    Cubic,
    Polyline,
    flatten,
    shapes,
    svg,
)
from clearmd.frontend.presenter.state import Tool

SVG = "{http://www.w3.org/2000/svg}"


def points_of(shape: Polyline | Circle | Cubic) -> tuple[tuple[float, float], ...]:
    if isinstance(shape, Circle):
        (x, y), r = shape.centre, shape.radius
        return ((x - r, y - r), (x + r, y + r))
    if isinstance(shape, Cubic):
        return (shape.start, shape.c1, shape.c2, shape.end)
    return shape.points


def test_every_tool_has_an_icon_inside_the_grid() -> None:
    assert set(ART) == {tool.value for tool in Tool}
    for tool in Tool:
        drawn = shapes(tool)
        assert drawn
        for shape in drawn:
            for x, y in points_of(shape):
                assert 0 <= x <= GRID and 0 <= y <= GRID


@pytest.mark.parametrize("tool", list(Tool))
def test_the_svg_has_one_element_per_shape_in_the_colour(tool: Tool) -> None:
    text = svg(tool, "#0F766E", 48)
    root = ET.fromstring(text)
    assert (
        root.tag == f"{SVG}svg" and root.get("width") == "48" and root.get("viewBox") == "0 0 24 24"
    )
    assert root.get("stroke") == "#0F766E" and root.get("fill") == "none"
    assert len(list(root)) == len(shapes(tool))


def test_the_colour_cannot_break_the_svg() -> None:
    root = ET.fromstring(svg("split", '"/><script/>', 24))
    assert [child.tag for child in root] == [f"{SVG}circle"] * 2 + [f"{SVG}polyline"] * 2


def test_a_curve_flattens_from_its_start_to_its_end() -> None:
    curve = Cubic((3, 3), (3, 11), (12, 9), (12, 15))
    points = flatten(curve, steps=8)
    assert len(points) == 9 and points[0] == (3, 3) and points[-1] == (12, 15)


def test_an_unknown_tool_is_an_error() -> None:
    with pytest.raises(KeyError):
        shapes("nonsense")
