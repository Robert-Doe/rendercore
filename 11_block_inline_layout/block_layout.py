"""
Module 11 — Block & Inline Layout
====================================
Proves: a tree of boxes can be assigned real, correct x/y/width/height
coordinates on a page — recursively, parent before child for POSITION,
but children before parent for an auto-height parent's SIZE. Both
directions happen inside the same recursive call, in the correct order,
without a separate two-pass algorithm.

Scope: this module lays out BLOCK-level boxes only (display: block,
stacked vertically — a "block formatting context"). Inline content and
text wrapping are Module 12's job entirely — see DECISIONS.md.
"""

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "06_dom_tree_builder"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "07_css_parser"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_cascade"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "10_box_model"))
from dom_tree_builder import parse_html, Element               # noqa: E402
from css_parser import parse_stylesheet                          # noqa: E402
from cascade import compute_all                                   # noqa: E402
from box_model import parse_length, _edges, Box, EdgeSizes        # noqa: E402


@dataclass
class ContainingBlock:
    x: float
    y: float        # for a child about to be laid out, this is the Y its MARGIN BOX starts at
    width: float


@dataclass
class LayoutBox:
    node: Element
    x: float          # content box origin
    y: float
    box: Box
    children: list = field(default_factory=list)

    @property
    def margin_box_height(self) -> float:
        return self.box.margin_box_height

    @property
    def border_box(self):
        """(x, y, width, height) of the border box — what Module 14/15
        will actually paint."""
        bx = self.x - self.box.padding.left - self.box.border.left
        by = self.y - self.box.padding.top - self.box.border.top
        return (bx, by, self.box.border_box_width, self.box.border_box_height)


def _resolve_size(spec, available: float, pad: float, bor: float, box_sizing: str):
    """Shared by width and height. `available` is the containing block's
    width for width, or None for height (auto height has a totally
    different rule — see below)."""
    if spec == "auto":
        if available is None:
            return None   # signals "compute from children" — height only
        return max(0.0, available - pad - bor)   # block auto-WIDTH fills the container
    if box_sizing == "border-box":
        return max(0.0, spec - pad - bor)
    return spec


def _is_block_child(node) -> bool:
    return isinstance(node, Element)


def layout_block(node: Element, containing_block: ContainingBlock, styles: dict) -> LayoutBox:
    style = styles[id(node)]
    box_sizing = style.get("box-sizing", "content-box")

    padding = _edges(style, "padding")
    border = _edges(style, "border", uniform_key="border-width")
    margin = _edges(style, "margin")

    width_spec = parse_length(style.get("width", "auto"), auto_allowed=True)
    height_spec = parse_length(style.get("height", "auto"), auto_allowed=True)

    # WIDTH: auto fills the containing block minus this box's own
    # margin/border/padding — a block box in normal flow always resolves
    # its own width; it never depends on its children the way height can.
    content_width = _resolve_size(
        width_spec, containing_block.width - margin.horizontal,
        padding.horizontal, border.horizontal, box_sizing,
    )

    content_x = containing_block.x + margin.left + border.left + padding.left
    content_y = containing_block.y + margin.top + border.top + padding.top

    # Lay out block-level children FIRST — recursion naturally computes
    # "children before parent" for height, while still handing each
    # child its position top-down, because Python's call stack does both
    # in the right order for free: we're already "inside" this box's
    # code, computing content_x/content_y, before we ever call layout on
    # a child; and we don't finish computing OUR OWN height until every
    # child call below has returned.
    children: list[LayoutBox] = []
    cursor_y = content_y
    for child in node.children:
        if not _is_block_child(child):
            continue
        child_style = styles.get(id(child))
        if not child_style or child_style.get("display") != "block":
            continue   # non-block children are Module 12's job entirely
        child_cb = ContainingBlock(x=content_x, y=cursor_y, width=content_width)
        child_box = layout_block(child, child_cb, styles)
        children.append(child_box)
        cursor_y += child_box.margin_box_height

    # HEIGHT: explicit value resolves like width; auto means "however
    # far the cursor moved while stacking children" — which is only
    # known now, after the loop above has run.
    if height_spec == "auto":
        content_height = cursor_y - content_y
    else:
        content_height = _resolve_size(height_spec, None, padding.vertical, border.vertical, box_sizing)
        if box_sizing == "border-box":
            content_height = max(0.0, height_spec - padding.vertical - border.vertical)
        else:
            content_height = height_spec

    box = Box(content_width, content_height, padding, border, margin)
    return LayoutBox(node=node, x=content_x, y=content_y, box=box, children=children)


def print_layout(lb: LayoutBox, depth: int = 0):
    indent = "  " * depth
    bx, by, bw, bh = lb.border_box
    tag = lb.node.tag
    ident = lb.node.attrs.get("id", "")
    label = f"<{tag}{' id=' + ident if ident else ''}>"
    print(f"{indent}{label:20s} border-box=({bx:.0f},{by:.0f}) {bw:.0f}x{bh:.0f}   "
          f"content=({lb.x:.0f},{lb.y:.0f}) {lb.box.content_width:.0f}x{lb.box.content_height:.0f}")
    for child in lb.children:
        print_layout(child, depth + 1)


def find(lb: LayoutBox, node_id: str):
    if lb.node.attrs.get("id") == node_id:
        return lb
    for c in lb.children:
        found = find(c, node_id)
        if found:
            return found
    return None


if __name__ == "__main__":
    html = """
    <body>
      <div id="outer">
        <div id="a">A</div>
        <div id="b">
          <div id="b1">B1</div>
          <div id="b2">B2</div>
        </div>
      </div>
    </body>
    """
    # No user-agent stylesheet exists in this course (see DECISIONS.md),
    # so "body, div { display: block }" has to be stated explicitly —
    # real browsers ship this rule invisibly, we don't.
    # NOTE: shorthand properties like "padding: 10px" are NOT expanded by
    # Module 7's parser (see Module 9's DECISIONS.md) — every side is
    # written out longhand here on purpose, not as a style preference.
    css = """
    body, div { display: block; }
    #outer { width: 400px; padding-top: 10px; padding-right: 10px;
              padding-bottom: 10px; padding-left: 10px; }
    #a { height: 50px; margin-bottom: 20px; }
    #b { border-width: 2px; padding-top: 5px; padding-right: 5px;
         padding-bottom: 5px; padding-left: 5px; }
    #b1 { height: 30px; }
    #b2 { height: 40px; margin-top: 10px; }
    """

    tree = parse_html(html)
    rules = parse_stylesheet(css)
    styles = compute_all(tree, rules)

    VIEWPORT_WIDTH = 800.0   # stand-in for a real viewport; see DECISIONS.md
    viewport = ContainingBlock(x=0, y=0, width=VIEWPORT_WIDTH)
    body_node = next(c for c in tree.children if isinstance(c, Element) and c.tag == "body")
    layout = layout_block(body_node, viewport, styles)

    print("=" * 70)
    print("Full layout tree (border box AND content box shown per node)")
    print("=" * 70)
    print_layout(layout)

    outer = find(layout, "outer")
    a = find(layout, "a")
    b = find(layout, "b")
    b1 = find(layout, "b1")
    b2 = find(layout, "b2")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"#outer content_width == explicit 400px (not stretched to 800): "
          f"{outer.box.content_width == 400.0}")
    print(f"#a content_width == outer's content_width, 400px (auto width "
          f"fills its containing block exactly, no padding/border/margin of "
          f"its own on the sides): {a.box.content_width == 400.0}")
    print(f"#a starts at y=outer.content_y (first child, no top margin): "
          f"{a.y == outer.y}")
    a_border_y = a.border_box[1]
    b_border_y = b.border_box[1]
    print(f"#b's BORDER BOX starts BELOW #a's full margin box (50 height + "
          f"20 margin-bottom = 70px lower than #a's border box): "
          f"{b_border_y - a_border_y == 70.0}")
    print(f"#b's auto content_height == sum of b1+b2's margin-box heights "
          f"(30 + 50) == 80 (computed from children BEFORE #b's own box is done): "
          f"{b.box.content_height == 80.0}")
    print(f"#outer's auto content_height == 164 (0 + #a's 70 + #b's 94 margin-box "
          f"heights, stacked): {outer.box.content_height == 164.0}")
