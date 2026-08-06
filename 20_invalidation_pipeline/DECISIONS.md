# DECISIONS.md — Module 20: Invalidation & Re-render Pipeline

Source file: `invalidation.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### The relayout boundary search starts at the mutated node's PARENT,
    never the node itself

**(a) Forced by logical necessity — and a real bug this module's own
development caught.** The first version of `find_relayout_boundary`
started its search AT the mutated node, which meant it immediately
"found" the mutated node's own (just-changed) height and returned the
node itself as the boundary — collapsing the whole algorithm into a
no-op, since re-laying-out a leaf in isolation, disconnected from its
parent's flow, doesn't correctly reposition anything. A node's own
height is exactly what just changed; it can never be evidence that
FURTHER change won't propagate outward from it. The fix — starting the
walk at `node.parent` — was necessary, not stylistic, and is now the
kind of bug this module's own docs exist to make visible rather than
bury.

### A relayout boundary is an ancestor with an EXPLICIT (non-auto) height

**(a) Forced by Module 11's own auto-height rule.** Module 11's
DECISIONS.md established that an `auto`-height block's size is computed
FROM its children — meaning any change inside it can, in principle,
change ITS size too, which could then change ITS parent's size, and so
on. An ancestor with an EXPLICIT height is the first point going upward
where that chain of "could this size change" provably stops — its own
box is defined by a fixed number, not by anything inside it. This isn't
a heuristic that's usually right; it's a direct logical consequence of
how Module 11 already defined explicit vs. auto sizing.

### Verification uses Python object identity (`is`), not equal field values

**(c) Our convention — and the module's central methodological point.**
Checking that `#sidebar`'s LayoutBox has the SAME field values before
and after invalidation would only prove the end RESULT looks unchanged —
it would pass even if the code fully rebuilt `#sidebar` from scratch and
happened to produce identical numbers. Checking `sidebar_layout_v2 is
sidebar_layout_v1` proves something strictly stronger: that object was
never recomputed at all, because it's literally the same Python object in
memory. This is the only kind of check that can distinguish "correctly
unaffected" from "recomputed but happened not to change."

### Re-layout re-runs Module 11's `layout_block` UNMODIFIED on just the
    boundary subtree, rather than a bespoke incremental algorithm

**(c) Our convention — reuse over reimplementation, same discipline as
Modules 4, 14, and 19.** Once the boundary is correctly identified, there
is nothing special about laying it out — it's exactly the same operation
Module 11 already performs on any subtree, just invoked on a smaller
root than "the whole page." No new layout logic exists in this module;
only the decision of WHERE to re-invoke Module 11's existing logic is
new.

### Partial re-paint is demonstrated via `build_display_list` on ONLY the
    boundary's `PaintBox`, without touching real canvas items

**(c) Our convention — an explicit scope boundary, not a claim of full
re-render integration.** Splicing specific canvas items in and out of a
live Tkinter canvas (deleting exactly the old boundary subtree's items,
adding exactly the new ones, leaving `#sidebar`'s real canvas items
untouched) is a straightforward extension using Module 15's `rasterize()`
on just this module's new display-list segment plus `canvas.delete()` on
the old items' ids — genuinely not hard, given everything already built,
but left as a natural next step rather than implemented here, so this
module's own scope stays focused on proving the layout-boundary algorithm
itself is correct.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Boundary search starts at the mutated node's PARENT (bug fixed here) | (a) forced by logical necessity |
| 2 | A relayout boundary = nearest ancestor with explicit height | (a) forced by Module 11's own auto-height rule |
| 3 | Verification uses object identity (`is`), not equal values | (c) the module's core methodological point |
| 4 | Re-layout reuses Module 11's `layout_block` unmodified | (c) reuse over reimplementation |
| 5 | Partial re-paint demonstrated via display list only, not live canvas splicing | (c) explicit scope boundary |

## What We Proved

A three-level-deep tree with two independent branches — `#sidebar` and
`#main` — was fully laid out once. A simulated script mutation changed
`#target` (deep inside `#main`) from 50px to 150px tall. The boundary
search correctly identified `#main` (not `#target` itself, not `#sidebar`,
not `body`) as the safe re-layout root — and, independently, `#main`'s
own height was confirmed to remain exactly 300px after re-layout,
concretely demonstrating WHY that boundary choice was safe. `#sidebar`
and its child `#sidebar_item`, entirely outside the boundary subtree,
were proven — by object identity, the strongest verification available —
to have never been recomputed at all. And a display list regenerated for
just the boundary subtree correctly reflected the new 150px height in
exactly 2 draw commands, not a full-page rebuild. See `tutorial.html`
section 06 for the full, unedited output, including the real
boundary-detection bug this module's own development caught and fixed.
Module 21 wraps this entire engine in an actual browser chrome — address
bar, tabs, and navigation history.
