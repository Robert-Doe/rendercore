"""
Module 14 — Paint / Display List
====================================
Proves: a laid-out tree can be flattened into an ordered, FLAT list of
primitive draw commands — reusing Module 13's paint_order() directly, so
z-index correctly reorders which box's commands appear first in the list,
not just which box "looks like" it's on top.

A flat list matters because Module 15's rasterizer will just replay this
list front-to-back with no knowledge of trees, parents, or CSS at all —
by the time we're here, every layout/style decision is already final.
"""

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "13_flexbox_stacking"))
from flex_and_stacking import StackItem, paint_order   # noqa: E402  -- REUSED, not reimplemented


@dataclass
class DrawRect:
    x: float
    y: float
    width: float
    height: float
    color: str

    def __repr__(self):
        return f"DrawRect(({self.x:.0f},{self.y:.0f}) {self.width:.0f}x{self.height:.0f}, {self.color})"


@dataclass
class DrawBorder:
    x: float
    y: float
    width: float
    height: float
    color: str
    border_width: float

    def __repr__(self):
        return f"DrawBorder(({self.x:.0f},{self.y:.0f}) {self.width:.0f}x{self.height:.0f}, {self.color}, {self.border_width}px)"


@dataclass
class DrawText:
    x: float
    y: float
    text: str
    color: str

    def __repr__(self):
        return f"DrawText(({self.x:.0f},{self.y:.0f}), {self.text!r}, {self.color})"


@dataclass
class PaintBox:
    """A minimal, self-contained stand-in for a real Module 11 LayoutBox
    + Module 9 computed style — everything this module actually needs
    to decide what to draw and in what order. See DECISIONS.md for why
    this module doesn't require the full pipeline wired together."""
    label: str
    x: float
    y: float
    width: float
    height: float
    background: str = None
    border_color: str = None
    border_width: float = 0.0
    z_index: int = None
    children: list = field(default_factory=list)


def build_display_list(box: PaintBox) -> list:
    """Flatten one box (and everything inside it) into draw commands, in
    the CORRECT paint order: this box's own background, then its border,
    THEN its children — reordered among themselves by Module 13's real
    z-index/document-order rule, not just left as DOM order."""
    items = []

    if box.background:
        items.append(DrawRect(box.x, box.y, box.width, box.height, box.background))
    if box.border_color and box.border_width > 0:
        items.append(DrawBorder(box.x, box.y, box.width, box.height,
                                 box.border_color, box.border_width))

    stack_items = [StackItem(label=c.label, z_index=c.z_index, tree_order=i)
                   for i, c in enumerate(box.children)]
    ordered = paint_order(stack_items)                     # <- Module 13, reused directly
    children_by_label = {c.label: c for c in box.children}

    for stacked in ordered:
        child = children_by_label[stacked.label]
        items.extend(build_display_list(child))             # depth-first: a box's own
                                                               # commands always precede
                                                               # anything from ITS children
    return items


if __name__ == "__main__":
    # root (gray bg)
    #  ├─ A  (z=0,  red bg)      1st in DOM
    #  ├─ B  (z=-1, blue bg)     2nd in DOM  -- should paint FIRST among siblings
    #  └─ C  (z=0,  green bg)    3rd in DOM
    #       └─ D (border only, no bg, purple 3px border)
    D = PaintBox("D", x=60, y=60, width=20, height=20, border_color="purple", border_width=3)
    A = PaintBox("A", x=0, y=0, width=50, height=50, background="red", z_index=0)
    B = PaintBox("B", x=10, y=10, width=50, height=50, background="blue", z_index=-1)
    C = PaintBox("C", x=20, y=20, width=50, height=50, background="green", z_index=0,
                 children=[D])
    root = PaintBox("root", x=0, y=0, width=200, height=200, background="gray",
                     children=[A, B, C])

    display_list = build_display_list(root)

    print("=" * 70)
    print("Flattened display list, in paint order")
    print("=" * 70)
    for i, item in enumerate(display_list):
        print(f"  [{i}] {item!r}")

    colors_in_order = [item.color for item in display_list]
    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"root's own background is drawn FIRST, before any child: "
          f"{colors_in_order[0] == 'gray'}")
    print(f"B (z=-1) painted before A and C (z=0) despite being 2nd in DOM: "
          f"{colors_in_order.index('blue') < colors_in_order.index('red')}")
    print(f"A painted before C — both z=0, DOM order (A then C) breaks the tie: "
          f"{colors_in_order.index('red') < colors_in_order.index('green')}")
    print(f"D's border command appears AFTER C's own background "
          f"(children paint after their own parent's commands): "
          f"{[type(i).__name__ for i in display_list].index('DrawBorder') > colors_in_order.index('green')}")
    print(f"the whole thing is a FLAT list (5 items: 4 rects + 1 border), "
          f"no nested structure: {len(display_list) == 5}")
