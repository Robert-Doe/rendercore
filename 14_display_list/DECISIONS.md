# DECISIONS.md — Module 14: Paint / Display List

Source file: `display_list.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### `paint_order()` is IMPORTED from Module 13, not reimplemented

**(c) Our convention — and the module's clearest example of reuse over
duplication.** This module needs exactly the same z-index/document-order
sorting Module 13 already built and verified. Writing a second, slightly
different sorting function here — even one that produced identical
results — would mean two places in the course that could silently drift
out of sync if either were changed later. `build_display_list()` imports
`StackItem` and `paint_order` directly and calls them unmodified,
the same discipline Module 4 used reusing Module 3's HTTP functions
unchanged.

### A box's OWN commands (background, then border) are always emitted
    BEFORE recursing into its children

**(a) Forced by real painting semantics, not a style choice.** A child
element is defined to visually sit ON TOP of its parent's background —
if a display list listed a child's paint commands before its own
parent's background fill, the parent's background would be drawn on top
of the child in a naive front-to-back renderer (Module 15), covering it
up entirely. Depth-first, "self before children," is the only ordering
that produces correct visual output from a simple sequential replay.

### Background is drawn before border, for the same box

**(b) External contract.** CSS defines the background as painting
"under" the border (a border can be semi-transparent or dashed, showing
background color through/between its segments) — background-then-border
is the real painting order, not an arbitrary pick between two equally
valid options.

### `PaintBox` is a small, self-contained stand-in, not Module 11's
    actual `LayoutBox` wired directly in

**(c) Our convention — matching how Module 13 stayed decoupled from a
real DOM.** This module's actual point — flattening a tree into an
ordered flat list, correctly respecting paint order — doesn't require
the full box-model/layout machinery to demonstrate or verify. `PaintBox`
carries only what `build_display_list()` actually reads: geometry,
paint-relevant style, z-index, and children. Wiring Module 11's real
`LayoutBox` (plus each node's computed style from Module 9) into this
exact function would be a small, mechanical adapter — not a change to
the algorithm itself.

### The display list is a flat Python list of dataclass instances, not a
    tree, not a generator

**(c) Our convention.** A generator would work for one-time consumption,
but a real display list is often diffed, filtered, or replayed more than
once (Module 16's compositing, and later invalidation in Module 20, both
want to inspect or partially rebuild it) — a concrete list is the more
honest representation of "the thing produced," even though it costs a
bit more memory than lazy generation would.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | `paint_order()` imported from Module 13, not reimplemented | (c) reuse over duplication |
| 2 | A box's own commands always precede its children's | (a) forced by real painting semantics |
| 3 | Background painted before border | (b) external contract |
| 4 | `PaintBox` is a decoupled stand-in, not the real `LayoutBox` | (c) convention, mirrors Module 13 |
| 5 | Concrete flat list, not a tree or generator | (c) convention |

## What We Proved

A small tree — a gray root containing three overlapping children with
mixed z-index values, one of which has its own bordered child — flattened
into exactly 5 draw commands in verifiably correct order: the root's own
background came first; the z=-1 child painted before its z=0 siblings
despite being second in document order; the two z=0 siblings painted in
their correct document order; and the nested child's border command
appeared only after its own parent's background, never before. See
`tutorial.html` section 06 for the full, unedited output. Module 15 takes
this exact flat list and replays it against a real Tkinter canvas —
turning draw COMMANDS into actual PIXELS for the first time in this
course.
