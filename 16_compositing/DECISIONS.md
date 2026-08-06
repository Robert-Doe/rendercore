# DECISIONS.md — Module 16: Compositing & Layers

Source file: `compositing.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Verification uses `canvas.find_overlapping()` at a real point, not
    display-list order or individual item properties

**(c) Our convention — the entire reason this module exists as separate
from Module 15.** Module 14 verified the display list's DATA is correctly
ordered. Module 15 verified each individual canvas item's properties
match its command. Neither of those checks can catch a bug where the
data is correct but something in between silently ignores it — for
example, a hypothetical rasterizer that painted items in DOM order
instead of display-list order would still pass every one of Module 15's
checks (each item would still exist with the right color and
coordinates), while producing a completely wrong final image. Querying
`find_overlapping()` at a real coordinate and checking which item Tk
itself reports as topmost is the only check in this course so far that
verifies the ACTUAL VISUAL RESULT, not just the data that was supposed to
produce it.

### The test scene is deliberately adversarial: the higher-z-index box is
    FIRST in the children list, not last

**(c) Our convention, chosen specifically to make the test meaningful.**
If the higher-z-index box had also happened to be later in the children
list, a broken "just paint in DOM order" implementation would accidentally
produce the correct-looking result anyway — the bug would be invisible.
Placing them in the OPPOSITE order (z-index says "paint me last," DOM
order says "paint me first") means only a genuinely z-index-aware pipeline
can pass this check; a DOM-order-only implementation would fail it
visibly, with the wrong color reported at the overlap point.

### `find_overlapping()`'s return order (bottom-to-top) is relied on
    directly — `stack_at_point[-1]` is treated as "the visible one"

**(b) External contract — this is Tk's own documented behavior for this
method,** and it was confirmed directly during this module's development
(a two-rectangle test showed the later-created item consistently last in
the returned tuple). This module's correctness claim rests on that
documented, verified ordering — not an assumption about how Tk happens to
behave today.

### This module does NOT implement real GPU layers or true parallel
    compositing

**(c) Our convention — explicit scope-out, already named in the
roadmap's Tools/Architecture Target.** Real browsers can promote specific
elements (video, transformed/animated elements) to their own GPU-backed
layer, composited together by the GPU rather than redrawn on a single 2D
surface every frame — a real performance technique with real complexity
(texture memory, layer invalidation, compositor threads). This course's
"compositing" is entirely: correct paint ORDER on one single Tk canvas.
Named explicitly so "Module 16: Compositing" isn't mistaken for a claim
of GPU-level layer compositing.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Verify via real canvas pixel query, not display-list/item data | (c) the module's core reason to exist |
| 2 | Test scene deliberately inverts DOM order vs. z-index order | (c) convention, makes the check meaningful |
| 3 | `find_overlapping()`'s bottom-to-top order relied on directly | (b) Tk's documented, verified behavior |
| 4 | No real GPU layers or parallel compositing implemented | (c) explicit scope-out |

## What We Proved

A red box (z-index 5, first in the DOM) and a blue box (z-index 1, second
in the DOM) were deliberately arranged so DOM order and z-index order
disagree about which should be on top. The display list correctly listed
blue before red (paint-order-aware). The rasterized canvas was then
queried DIRECTLY — not the display list, not individual item properties —
at a real point inside both boxes' overlapping region, and Tk itself
reported red as the topmost, visible item. This is the first fully
end-to-end, pixel-level verification in this course: bytes fetched over
a real network (Modules 1-4) became a real DOM (Modules 5-6), a real
computed style (Modules 7-9), real geometry (Modules 10-13), a real
ordered display list (Module 14), real canvas items (Module 15), and now
a real, independently-verified correct VISIBLE RESULT. This completes
Track 1 — a full, working, static rendering engine. Track 2 begins with
Module 17, making this pipeline respond to something other than a script
telling it what to render once.
