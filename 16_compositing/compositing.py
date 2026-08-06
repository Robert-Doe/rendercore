"""
Module 16 — Compositing & Layers
====================================
Proves: overlapping elements produce the CORRECT VISIBLE result — verified
at the pixel level via Tk's own `find_overlapping`, not just "the display
list has the right order" (Module 14 already proved that) or "each item
individually has the right properties" (Module 15 already proved that).

This is the module that would actually catch a bug where paint order was
computed correctly as DATA but something downstream silently painted in
DOM order anyway — the two previous modules could both still report
"success" while the final image was wrong. This module checks the image.
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "14_display_list"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "15_rasterizer"))
from display_list import PaintBox, build_display_list   # noqa: E402
from rasterizer import rasterize                          # noqa: E402


if __name__ == "__main__":
    # Deliberately adversarial scene: "first_in_dom" is declared FIRST in
    # the children list (so naive "paint in list order" would put it
    # UNDERNEATH), but it has a HIGHER z-index. Correct compositing must
    # still put it on TOP, despite DOM order suggesting the opposite.
    first_in_dom = PaintBox("first_in_dom", x=0, y=0, width=100, height=100,
                             background="red", z_index=5)
    second_in_dom = PaintBox("second_in_dom", x=50, y=50, width=100, height=100,
                              background="blue", z_index=1)
    root_box = PaintBox("root", x=0, y=0, width=200, height=200,
                         children=[first_in_dom, second_in_dom])

    display_list = build_display_list(root_box)

    print("=" * 70)
    print("Display list order (Module 14's output)")
    print("=" * 70)
    for i, cmd in enumerate(display_list):
        print(f"  [{i}] {cmd!r}")
    print("\nNote: 'blue' (lower z-index) is painted FIRST in this list, even")
    print("though 'first_in_dom' (red) appears FIRST in the children list —")
    print("paint order already overrode DOM order as DATA. This module checks")
    print("whether that data actually produces the right PIXELS.")

    root = tk.Tk()
    root.withdraw()
    canvas = tk.Canvas(root, width=200, height=200, bg="white")
    canvas.pack()
    item_ids = rasterize(canvas, display_list)
    root.update()

    # The two boxes overlap in the region (50,50)-(100,100). Pick a point
    # solidly inside that overlap and ask Tk, directly, what's really there.
    overlap_point = (75, 75)
    stack_at_point = canvas.find_overlapping(*overlap_point, *overlap_point)
    topmost_item = stack_at_point[-1]   # find_overlapping returns bottom-to-top
    topmost_color = canvas.itemcget(topmost_item, "fill")

    print()
    print("=" * 70)
    print(f"Querying REAL canvas state at overlap point {overlap_point}")
    print("=" * 70)
    print(f"items at this point, bottom-to-top: {stack_at_point}")
    print(f"topmost (actually VISIBLE) item id: {topmost_item}")
    print(f"topmost item's fill color: {topmost_color!r}")

    print()
    print("=" * 70)
    print("Checks")
    print("=" * 70)
    print(f"both overlapping items are present at the shared point: "
          f"{len(stack_at_point) == 2}")
    print(f"the VISIBLE (topmost) color at the overlap is RED — the higher "
          f"z-index item — even though it was FIRST in the DOM/children list: "
          f"{topmost_color == 'red'}")
    print(f"if this module had naively painted in DOM/list order instead of "
          f"z-index-aware paint order, the topmost color would have been "
          f"'blue' instead — the exact bug this check exists to catch.")

    root.destroy()
