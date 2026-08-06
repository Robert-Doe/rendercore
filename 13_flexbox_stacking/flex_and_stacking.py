"""
Module 13 — Stacking & a Flexbox Subset
==========================================
Two independent things that both live outside "normal flow," proved
separately:

PART A — a flex container distributes leftover space among children
along the main axis, proportional to flex-grow.

PART B — paint order for overlapping elements is decided by z-index,
NOT by document order — except when z-index ties, at which point
document order is exactly what breaks the tie.
"""

from dataclasses import dataclass


# ============================================================ PART A: FLEX


@dataclass
class FlexItem:
    label: str
    flex_grow: float
    basis: float   # this module treats an item's declared width as its
                    # flex-basis stand-in — see DECISIONS.md for what real
                    # flex-basis/content-sizing this simplifies away


@dataclass
class FlexResult:
    label: str
    x: float
    width: float


def layout_flex_row(items: list, container_width: float) -> list:
    """Single-line, row-direction, no-wrap flex layout: give every item
    its basis width, then distribute whatever's left over proportionally
    by flex-grow. An item with flex_grow=0 never grows past its basis,
    which is the real spec's default — flex items do NOT stretch to fill
    the container unless something asks them to."""
    total_basis = sum(item.basis for item in items)
    free_space = max(0.0, container_width - total_basis)
    total_grow = sum(item.flex_grow for item in items)

    results = []
    x = 0.0
    for item in items:
        extra = (free_space * item.flex_grow / total_grow) if total_grow > 0 else 0.0
        width = item.basis + extra
        results.append(FlexResult(label=item.label, x=x, width=width))
        x += width
    return results


# ======================================================= PART B: STACKING


@dataclass
class StackItem:
    label: str
    z_index: int | None   # None = "auto" — treated as z=0 for sorting,
                            # see DECISIONS.md for the real distinction this loses
    tree_order: int         # position in document/DOM order


def paint_order(items: list) -> list:
    """Sort into PAINT order: lowest z-index first (painted first =
    furthest back), highest z-index last (painted last = on top). Ties
    in z-index are broken by tree_order — later in the document paints
    on top of earlier siblings at the same z-index."""
    def sort_key(item: StackItem):
        z = item.z_index if item.z_index is not None else 0
        return (z, item.tree_order)
    return sorted(items, key=sort_key)


if __name__ == "__main__":
    print("=" * 70)
    print("PART A, CASE 1 — three items, flex-grow 1:2:1, extra space split proportionally")
    print("=" * 70)
    items1 = [
        FlexItem("left", flex_grow=1, basis=100),
        FlexItem("center", flex_grow=2, basis=100),
        FlexItem("right", flex_grow=1, basis=100),
    ]
    result1 = layout_flex_row(items1, container_width=600)
    for r in result1:
        print(f"  {r.label:8s} x={r.x:6.1f}  width={r.width:6.1f}")

    print(f"\nwidths sum to exactly the container width (600): "
          f"{sum(r.width for r in result1) == 600.0}")
    print(f"'center' (grow=2) got exactly twice the extra space of 'left'/'right' "
          f"(grow=1 each): {result1[1].width - 100 == 2 * (result1[0].width - 100)}")

    print()
    print("=" * 70)
    print("PART A, CASE 2 — flex-grow all 0: items DON'T stretch to fill the container")
    print("=" * 70)
    items2 = [FlexItem("a", flex_grow=0, basis=100), FlexItem("b", flex_grow=0, basis=100),
              FlexItem("c", flex_grow=0, basis=100)]
    result2 = layout_flex_row(items2, container_width=600)
    for r in result2:
        print(f"  {r.label:8s} x={r.x:6.1f}  width={r.width:6.1f}")
    print(f"\nno item grew past its basis width (100) despite 300px of unused "
          f"space in a 600px container: {all(r.width == 100.0 for r in result2)}")

    print()
    print("=" * 70)
    print("PART B — paint order: z-index overrides document order, ties broken BY document order")
    print("=" * 70)
    stack_items = [
        StackItem("A (z=2, 1st in DOM)", z_index=2, tree_order=0),
        StackItem("B (z=auto, 2nd in DOM)", z_index=None, tree_order=1),
        StackItem("C (z=-1, 3rd in DOM)", z_index=-1, tree_order=2),
        StackItem("D (z=2, 4th in DOM)", z_index=2, tree_order=3),
        StackItem("E (z=0, 5th in DOM)", z_index=0, tree_order=4),
    ]
    order = paint_order(stack_items)
    for i, item in enumerate(order):
        print(f"  paint step {i}: {item.label}")

    labels_in_order = [item.label for item in order]
    print(f"\nC (z=-1) painted FIRST despite being 3rd in the DOM: "
          f"{labels_in_order[0].startswith('C')}")
    print(f"B (z=auto/0) painted before E (z=0) — DOM order breaks the z=0 tie: "
          f"{labels_in_order.index('B (z=auto, 2nd in DOM)') < labels_in_order.index('E (z=0, 5th in DOM)')}")
    print(f"A (z=2) painted before D (z=2) — DOM order breaks the z=2 tie: "
          f"{labels_in_order.index('A (z=2, 1st in DOM)') < labels_in_order.index('D (z=2, 4th in DOM)')}")
    print(f"Both z=2 items (A, D) painted LAST — on top of everything else: "
          f"{labels_in_order[-2:] == ['A (z=2, 1st in DOM)', 'D (z=2, 4th in DOM)']}")
