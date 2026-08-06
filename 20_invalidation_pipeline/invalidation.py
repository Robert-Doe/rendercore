"""
Module 20 — Invalidation & Re-render Pipeline
=================================================
Proves: a style mutation on ONE node triggers correct re-layout of only
the affected subtree — bounded at the nearest ancestor with an EXPLICIT
(non-auto) height, since that ancestor's own size can't change no matter
what its children do — while everything outside that subtree is not
just "unaffected in the end result" but literally NEVER RECOMPUTED:
proven via Python object identity (`is`), not just equal values.

This module does not modify Modules 9, 11, 14, or 19 — it composes them.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "06_dom_tree_builder"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "07_css_parser"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_cascade"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "11_block_inline_layout"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "14_display_list"))
from dom_tree_builder import parse_html, Element                     # noqa: E402
from css_parser import parse_stylesheet                                # noqa: E402
from cascade import compute_all                                        # noqa: E402
from block_layout import layout_block, ContainingBlock, LayoutBox       # noqa: E402
from display_list import PaintBox, build_display_list                  # noqa: E402


def find_relayout_boundary(node: Element, styles: dict) -> Element:
    """Walk UP from the mutated node's PARENT (never the node itself —
    its own height is exactly what just changed, so it can never be its
    own boundary) looking for the nearest ANCESTOR with an EXPLICIT
    height. That ancestor's own size is guaranteed not to change no
    matter what happens inside it — which is exactly what makes it safe
    to stop re-layout there instead of continuing all the way to the
    document root. If nothing has an explicit height, the walk simply
    reaches the top — a real, correctly conservative fallback."""
    current = node.parent
    last_seen = current if current is not None else node
    while current is not None:
        style = styles.get(id(current), {})
        if style.get("height", "auto") != "auto":
            return current
        last_seen = current
        current = current.parent
    return last_seen   # no explicit-height ancestor found; fall back to the topmost one


def layout_box_to_paint_box(lb: LayoutBox, styles: dict) -> PaintBox:
    """Small, deliberately thin adapter from Module 11's LayoutBox to
    Module 14's PaintBox — see DECISIONS.md for why they're kept
    separate structures rather than merged into one."""
    style = styles.get(id(lb.node), {})
    bx, by, bw, bh = lb.border_box
    return PaintBox(
        label=lb.node.attrs.get("id", lb.node.tag),
        x=bx, y=by, width=bw, height=bh,
        background=style.get("background-color"),
        children=[layout_box_to_paint_box(c, styles) for c in lb.children],
    )


def find_layout_box(root: LayoutBox, dom_node: Element):
    if root.node is dom_node:
        return root
    for child in root.children:
        found = find_layout_box(child, dom_node)
        if found is not None:
            return found
    return None


if __name__ == "__main__":
    html = """
    <body>
      <div id="sidebar"><div id="sidebar_item">nav</div></div>
      <div id="main"><div id="target">original</div></div>
    </body>
    """
    css = """
    body, div { display: block; }
    #sidebar { }
    #sidebar_item { height: 80px; background-color: gray; }
    #main { width: 400px; height: 300px; background-color: white; }
    #target { height: 50px; background-color: red; }
    """

    document = parse_html(html)
    rules = parse_stylesheet(css)
    styles = compute_all(document, rules)

    body_node = next(c for c in document.children if isinstance(c, Element) and c.tag == "body")
    viewport = ContainingBlock(x=0, y=0, width=800)

    print("=" * 70)
    print("INITIAL full layout")
    print("=" * 70)
    body_layout = layout_block(body_node, viewport, styles)

    sidebar_node = next(c for c in body_node.children if isinstance(c, Element) and c.attrs.get("id") == "sidebar")
    main_node = next(c for c in body_node.children if isinstance(c, Element) and c.attrs.get("id") == "main")
    target_node = next(c for c in main_node.children if isinstance(c, Element) and c.attrs.get("id") == "target")

    sidebar_node_item = next(c for c in sidebar_node.children if isinstance(c, Element) and c.attrs.get("id") == "sidebar_item")
    sidebar_layout_v1 = find_layout_box(body_layout, sidebar_node)
    sidebar_item_layout_v1 = find_layout_box(body_layout, sidebar_node_item)
    main_layout_v1 = find_layout_box(body_layout, main_node)
    target_layout_v1 = find_layout_box(body_layout, target_node)
    print(f"  #target initial content_height: {target_layout_v1.box.content_height}")
    print(f"  #main   initial content_height: {main_layout_v1.box.content_height}  (explicit 300px)")

    print()
    print("=" * 70)
    print("MUTATION — a script changes #target's height from 50px to 150px")
    print("=" * 70)
    styles[id(target_node)]["height"] = "150px"   # simulates a JS style mutation (Module 19-style)

    boundary = find_relayout_boundary(target_node, styles)
    print(f"  relayout boundary found by walking up from #target: "
          f"#{boundary.attrs.get('id', boundary.tag)}")
    print(f"  found generically by find_relayout_boundary() — this test "
          f"asserts it's #main below, it isn't hardcoded here: "
          f"boundary is main_node = {boundary is main_node}")

    # Re-run layout ONLY on the boundary subtree, using ITS original
    # containing block (unchanged, since #main's own box doesn't move or
    # resize as a result of anything inside it — that guarantee is
    # EXACTLY what find_relayout_boundary looked for).
    boundary_layout_v1 = find_layout_box(body_layout, boundary)
    boundary_containing_block = ContainingBlock(
        x=boundary_layout_v1.x - boundary_layout_v1.box.padding.left - boundary_layout_v1.box.border.left,
        y=boundary_layout_v1.y - boundary_layout_v1.box.padding.top - boundary_layout_v1.box.border.top,
        width=800,   # the boundary's containing block is body's content box, still 800 wide
    )
    new_main_layout = layout_block(boundary, boundary_containing_block, styles)

    # Splice the new subtree back into the existing tree structure —
    # everything else in body_layout.children is left completely alone.
    main_index = body_layout.children.index(boundary_layout_v1)
    body_layout.children[main_index] = new_main_layout

    new_target_layout = find_layout_box(new_main_layout, target_node)

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"#target's NEW content_height reflects the mutation (150): "
          f"{new_target_layout.box.content_height == 150.0}")
    print(f"#main's OWN content_height is STILL 300 (explicit — the "
          f"child's growth did not change it, which is WHY it's a safe "
          f"boundary): {new_main_layout.box.content_height == 300.0}")

    sidebar_layout_v2 = find_layout_box(body_layout, sidebar_node)
    print(f"#sidebar's LayoutBox is the LITERAL SAME OBJECT as before the "
          f"mutation — never recomputed at all (proven by identity, not "
          f"just equal values): {sidebar_layout_v2 is sidebar_layout_v1}")

    sidebar_item_layout_v2 = find_layout_box(body_layout, sidebar_node_item)
    print(f"#sidebar_item (nested inside the untouched #sidebar) is ALSO "
          f"the literal same object as before — the identity guarantee "
          f"holds recursively down the whole untouched subtree: "
          f"{sidebar_item_layout_v2 is sidebar_item_layout_v1}")

    print()
    print("=" * 70)
    print("Partial RE-PAINT: regenerate a display list for ONLY the")
    print("boundary subtree — #sidebar's paint commands are never rebuilt")
    print("=" * 70)
    new_paint_subtree = layout_box_to_paint_box(new_main_layout, styles)
    new_display_list = build_display_list(new_paint_subtree)
    for cmd in new_display_list:
        print(f"  {cmd!r}")
    target_rect = next(c for c in new_display_list if c.height == 150.0)
    print(f"\nthe re-painted #target rectangle reflects the new 150px height: "
          f"{target_rect.height == 150.0}")
    print(f"only 2 draw commands were regenerated (main + target), NOT the "
          f"whole page: {len(new_display_list) == 2}")
