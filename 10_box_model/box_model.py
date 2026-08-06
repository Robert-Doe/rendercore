"""
Module 10 — The Box Model
============================
Proves: every styled node gets a computed content/padding/border/margin
box, and — the actual point of this module — that `box-sizing` isn't a
cosmetic detail. It changes what the `width` property NUMBER MEANS,
which means it has to be resolved before content width can be computed
at all. Get the order backwards and every box-sizing:border-box element
comes out the wrong size.
"""

from dataclasses import dataclass


def parse_length(value: str, auto_allowed: bool = False):
    """Parse a CSS length. Only bare numbers and 'px' values are
    supported — see DECISIONS.md for why percentages, em, and other
    units are explicitly out of scope for this module."""
    value = (value or "").strip()
    if value == "auto":
        return "auto" if auto_allowed else 0.0
    if not value:
        return 0.0
    if value.endswith("px"):
        value = value[:-2]
    try:
        return float(value)
    except ValueError:
        return 0.0   # unrecognized unit: treated as 0, not an error — see DECISIONS.md


@dataclass
class EdgeSizes:
    top: float = 0.0
    right: float = 0.0
    bottom: float = 0.0
    left: float = 0.0

    @property
    def horizontal(self) -> float:
        return self.left + self.right

    @property
    def vertical(self) -> float:
        return self.top + self.bottom


@dataclass
class Box:
    content_width: float
    content_height: float
    padding: EdgeSizes
    border: EdgeSizes
    margin: EdgeSizes

    # Each box "expands outward" one layer at a time — see the diagram
    # in tutorial.html. Every one of these properties is defined purely
    # in terms of the one before it.
    @property
    def padding_box_width(self) -> float:
        return self.content_width + self.padding.horizontal

    @property
    def padding_box_height(self) -> float:
        return self.content_height + self.padding.vertical

    @property
    def border_box_width(self) -> float:
        return self.padding_box_width + self.border.horizontal

    @property
    def border_box_height(self) -> float:
        return self.padding_box_height + self.border.vertical

    @property
    def margin_box_width(self) -> float:
        return self.border_box_width + self.margin.horizontal

    @property
    def margin_box_height(self) -> float:
        return self.border_box_height + self.margin.vertical


def _edges(style: dict, prefix: str, uniform_key: str | None = None) -> EdgeSizes:
    """Read four-sided values like padding-top/right/bottom/left. If
    `uniform_key` is given (used for border-width, which this module
    treats as one value on all four sides — see DECISIONS.md), that
    single property is used for all four edges instead."""
    if uniform_key:
        w = parse_length(style.get(uniform_key, "0"))
        return EdgeSizes(w, w, w, w)
    return EdgeSizes(
        top=parse_length(style.get(f"{prefix}-top", "0")),
        right=parse_length(style.get(f"{prefix}-right", "0")),
        bottom=parse_length(style.get(f"{prefix}-bottom", "0")),
        left=parse_length(style.get(f"{prefix}-left", "0")),
    )


def compute_box(style: dict) -> Box:
    """The order of operations that makes this module's whole point:
    box-sizing MUST be read before content width/height can be computed,
    because it changes what the `width`/`height` NUMBERS mean."""
    box_sizing = style.get("box-sizing", "content-box")   # default per spec
    width_spec = parse_length(style.get("width", "auto"), auto_allowed=True)
    height_spec = parse_length(style.get("height", "auto"), auto_allowed=True)

    padding = _edges(style, "padding")
    border = _edges(style, "border", uniform_key="border-width")
    margin = _edges(style, "margin")

    def resolve(spec, pad, bor):
        if spec == "auto":
            # Real auto-width resolution depends on the containing
            # block's available width — that's not known here. This
            # module deliberately stops at 0.0 and hands the real
            # resolution to Module 11. See DECISIONS.md and tutorial.html 05.
            return 0.0
        if box_sizing == "border-box":
            return max(0.0, spec - pad - bor)
        return spec   # content-box (the default): the number IS the content size

    content_width = resolve(width_spec, padding.horizontal, border.horizontal)
    content_height = resolve(height_spec, padding.vertical, border.vertical)

    return Box(content_width, content_height, padding, border, margin)


if __name__ == "__main__":
    shared = {
        "width": "300px", "height": "150px",
        "padding-top": "20px", "padding-right": "20px",
        "padding-bottom": "20px", "padding-left": "20px",
        "border-width": "5px",
        "margin-top": "10px", "margin-right": "10px",
        "margin-bottom": "10px", "margin-left": "10px",
    }

    content_box_style = {**shared, "box-sizing": "content-box"}
    border_box_style = {**shared, "box-sizing": "border-box"}
    auto_style = {"box-sizing": "content-box"}   # width/height both "auto"

    box_content = compute_box(content_box_style)
    box_border = compute_box(border_box_style)
    box_auto = compute_box(auto_style)

    print("=" * 70)
    print("content-box (the default) — 'width: 300px' means the CONTENT is 300px")
    print("=" * 70)
    print(f"  content:      {box_content.content_width} x {box_content.content_height}")
    print(f"  padding box:  {box_content.padding_box_width} x {box_content.padding_box_height}")
    print(f"  border box:   {box_content.border_box_width} x {box_content.border_box_height}")
    print(f"  margin box:   {box_content.margin_box_width} x {box_content.margin_box_height}")

    print()
    print("=" * 70)
    print("border-box — the SAME declared width/padding/border, different meaning")
    print("=" * 70)
    print(f"  content:      {box_border.content_width} x {box_border.content_height}")
    print(f"  padding box:  {box_border.padding_box_width} x {box_border.padding_box_height}")
    print(f"  border box:   {box_border.border_box_width} x {box_border.border_box_height}")
    print(f"  margin box:   {box_border.margin_box_width} x {box_border.margin_box_height}")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"content-box: content_width == declared 300px: {box_content.content_width == 300.0}")
    print(f"content-box: border_box_width == 300 + 2*20 + 2*5 == 350: "
          f"{box_content.border_box_width == 350.0}")

    print(f"border-box: content_width == 300 - 2*20 - 2*5 == 250: "
          f"{box_border.content_width == 250.0}")
    print(f"border-box: border_box_width == the DECLARED 300px exactly "
          f"(the defining property of border-box): {box_border.border_box_width == 300.0}")

    print(f"content-box vs border-box give DIFFERENT content widths from "
          f"IDENTICAL input, purely from box-sizing: "
          f"{box_content.content_width != box_border.content_width}")

    print(f"width: auto resolves to content_width=0.0 here (real resolution "
          f"deferred to Module 11, which knows the container): "
          f"{box_auto.content_width == 0.0}")
