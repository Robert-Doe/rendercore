# DECISIONS.md — Module 15: Rasterization to Canvas (Tkinter)

Source file: `rasterizer.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Tkinter's `Canvas` is used as-is; rasterization itself is not implemented

**(a) Forced by platform, treated as "hardware" — the same category as
`socket` and `ssl`.** Actually converting shapes into individual pixels
(scan-converting a rectangle, anti-aliasing a diagonal line, rendering a
font's glyph outlines) is real graphics-programming depth this course
scopes out entirely, the same way TLS's cryptography was scoped out in
Module 4. `Canvas.create_rectangle` and `Canvas.create_text` are Tk's
own primitives, backed by the OS's real windowing/graphics stack.

### `DrawRect` maps to `create_rectangle(..., outline="")`, `DrawBorder`
    maps to `create_rectangle(..., fill="")`

**(b) External contract — Tk's own primitive set.** Tkinter has one
shape primitive that can be filled, outlined, or both — there's no
separate "filled rect" vs. "outlined rect" object type to choose between.
Setting `outline=""` for a background fill and `fill=""` for a border
isn't an approximation of two different Tk features; it's the correct,
idiomatic way to use Tk's single rectangle primitive for two different
visual purposes.

### Verification uses `canvas.coords()`, not `canvas.bbox()`

**(c) Our convention, motivated by a real, verified Tk behavior worth
naming explicitly.** `canvas.bbox(item)` was tested directly against this
module's own output and confirmed to pad its returned box by roughly one
pixel on each side, REGARDLESS of whether the item has a visible outline
(`create_rectangle(10,10,60,60, outline="")` produced `bbox() ==
(9,9,61,61)`, not `(10,10,60,60)`) — this is Tk's own selection-hit-testing
margin, not a bug in this module. `canvas.coords(item)`, by contrast,
returned the exact input coordinates in every test run. Using `coords()`
for verification isn't a workaround for a limitation of this module — the
"limitation" is a real, confirmed property of the library being wrapped,
and `coords()` is simply the correct tool for exact-value verification.

### The Tk root window is created and then withdrawn (`root.withdraw()`)
    for this module's automated run

**(c) Our convention, specific to automated verification, not general
usage.** This module's own checks need to run without a human watching a
window appear — `withdraw()` hides the window while Tk still fully
processes all drawing calls underneath it, so `canvas.coords()` /
`canvas.type()` / `canvas.itemcget()` all report real, fully-computed
state. Module 21 (the real chrome UI) will NOT withdraw its window —
withdrawing here is purely a testing convenience for this module,
explicitly not the pattern a real running browser would follow.

### `root.update()` is called before inspecting canvas state

**(a) Forced by Tk's own execution model.** Tkinter's canvas operations
are processed through Tk's event loop, not synchronously the instant
`create_rectangle` returns. Querying canvas state before giving Tk a
chance to process pending drawing operations (`update()`, or normally the
running main event loop) risks inspecting stale or incomplete state —
this isn't a defensive habit, it's necessary for the checks below it to
be querying real, finished results.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Tk's `Canvas` used directly; no rasterization implemented ourselves | (a) treated as hardware |
| 2 | `DrawRect`/`DrawBorder` both map to `create_rectangle`, fill vs. outline | (b) Tk's own primitive shape |
| 3 | Verification uses `coords()`, not `bbox()` | (c) convention, based on a confirmed real Tk quirk |
| 4 | Window withdrawn for automated verification only | (c) convention, testing-specific |
| 5 | `root.update()` called before inspecting canvas state | (a) forced by Tk's event-driven execution model |

## What We Proved

Module 14's exact 5-command display list, replayed against a real
Tkinter `Canvas`, produced 5 real canvas items — queried back from Tk
itself, not from the original display list — with exactly matching
geometry (`coords()`), exactly matching fill and outline colors
(`itemcget()`), and correct Tk item types (`'rectangle'` for both filled
and outline-only boxes). This is the first module in the entire course
where the artifact under test is not a Python data structure but real
state inside a graphics library. See `tutorial.html` section 06 for the
full, unedited output. Module 16 adds the one thing this module doesn't
yet handle at all: multiple items whose visual stacking has to be
verified as correct, not just individually present.
