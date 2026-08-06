"""
Module 15 — Rasterization to Canvas (Tkinter)
=================================================
Proves: Module 14's display list, replayed against a REAL Tkinter
canvas, produces real canvas items with the exact geometry and colors
the display list specified — the first module in this course where
something other than Python data structures gets produced.

Tkinter is treated as "hardware" (see roadmap Tools/Architecture Target):
it wraps the OS's native windowing system and 2D drawing. We call three
of its drawing primitives (create_rectangle, create_text) — we do not
implement rasterization, anti-aliasing, or font rendering ourselves.
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "14_display_list"))
from display_list import DrawRect, DrawBorder, DrawText, build_display_list, PaintBox  # noqa: E402


def rasterize(canvas: tk.Canvas, display_list: list) -> list:
    """Replay a display list against a real canvas, front-to-back, in
    the exact order given — the rasterizer has NO knowledge of trees,
    z-index, or CSS; by this point, all of that is already baked into
    the list's order (Module 14's whole job)."""
    item_ids = []
    for cmd in display_list:
        if isinstance(cmd, DrawRect):
            item_id = canvas.create_rectangle(
                cmd.x, cmd.y, cmd.x + cmd.width, cmd.y + cmd.height,
                fill=cmd.color, outline="",
            )
        elif isinstance(cmd, DrawBorder):
            item_id = canvas.create_rectangle(
                cmd.x, cmd.y, cmd.x + cmd.width, cmd.y + cmd.height,
                fill="", outline=cmd.color, width=cmd.border_width,
            )
        elif isinstance(cmd, DrawText):
            item_id = canvas.create_text(
                cmd.x, cmd.y, text=cmd.text, fill=cmd.color, anchor="nw",
            )
        else:
            raise ValueError(f"rasterizer has no handler for {type(cmd).__name__}")
        item_ids.append(item_id)
    return item_ids


if __name__ == "__main__":
    # Same small overlapping-boxes scene as Module 14, so this module's
    # output is directly checkable against that one's already-verified list.
    D = PaintBox("D", x=60, y=60, width=20, height=20, border_color="purple", border_width=3)
    A = PaintBox("A", x=0, y=0, width=50, height=50, background="red", z_index=0)
    B = PaintBox("B", x=10, y=10, width=50, height=50, background="blue", z_index=-1)
    C = PaintBox("C", x=20, y=20, width=50, height=50, background="green", z_index=0, children=[D])
    root_box = PaintBox("root", x=0, y=0, width=200, height=200, background="gray", children=[A, B, C])
    display_list = build_display_list(root_box)

    root = tk.Tk()
    root.withdraw()   # no visible window needed for this automated check —
                       # in real use (Module 21's chrome UI) this stays shown
    canvas = tk.Canvas(root, width=200, height=200, bg="white")
    canvas.pack()

    item_ids = rasterize(canvas, display_list)
    root.update()   # forces Tk to actually process the draw calls

    print("=" * 70)
    print("Real Tkinter canvas items created from the display list")
    print("=" * 70)
    for cmd, item_id in zip(display_list, item_ids):
        kind = canvas.type(item_id)
        coords = canvas.coords(item_id)
        print(f"  item {item_id}: tk type={kind!r}  coords={coords}  <- from {cmd!r}")

    print()
    print("=" * 70)
    print("Checks — real queries against the real canvas, not the display list")
    print("=" * 70)
    print(f"one canvas item created per display-list command: "
          f"{len(item_ids) == len(display_list)}")

    rect_item = item_ids[0]   # root's gray background
    print(f"root's background item is a real Tk 'rectangle': "
          f"{canvas.type(rect_item) == 'rectangle'}")
    print(f"its EXACT coords match the command (10px Tk outline padding in "
          f"bbox() does NOT affect coords() — see tutorial.html 08): "
          f"{canvas.coords(rect_item) == [0.0, 0.0, 200.0, 200.0]}")
    print(f"its fill color matches the command exactly: "
          f"{canvas.itemcget(rect_item, 'fill') == 'gray'}")

    border_item = item_ids[-1]   # D's border
    print(f"D's border item is ALSO a Tk 'rectangle' (outline-only, no fill): "
          f"{canvas.type(border_item) == 'rectangle' and canvas.itemcget(border_item, 'fill') == ''}")
    print(f"its outline color and width match the command: "
          f"{canvas.itemcget(border_item, 'outline') == 'purple' and canvas.itemcget(border_item, 'width') == '3.0'}")

    root.destroy()
