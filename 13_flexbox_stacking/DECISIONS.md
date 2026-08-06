# DECISIONS.md — Module 13: Stacking & a Flexbox Subset

Source file: `flex_and_stacking.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

## Part A — Flexbox

### Extra space is distributed PROPORTIONALLY to `flex-grow`, not split evenly

**(a) Forced by spec.** `flex-grow` is explicitly defined as a ratio, not
a boolean "does this item grow." An item with `flex-grow: 2` is defined
to receive exactly twice the free space of a sibling with
`flex-grow: 1` — `extra = free_space * item.flex_grow / total_grow`
is that ratio, directly. Splitting space evenly among any item with a
nonzero grow value would not be flexbox; it would be a different,
simpler algorithm that happens to look similar in the common case where
all grow values are equal.

### `flex-grow: 0` (the default) means an item NEVER grows past its basis,
    even with unused space in the container

**(a) Forced by spec.** This is real flexbox's actual default behavior,
and it surprises people who expect flex children to automatically fill
their container — they don't, unless `flex-grow` says so. Case 2 exists
specifically to make this default visible and verified, not just
asserted.

### An item's declared `width` stands in for its flex-basis, with no
    content-based sizing

**(c) Our convention — a real, named simplification.** The actual flex
sizing algorithm is one of the most involved parts of the CSS spec:
`flex-basis` can be `auto` (falling back to the item's own `width`, which
can itself fall back to its CONTENT's intrinsic size — requiring text
measurement, exactly the kind of thing Module 12 handles), and the full
algorithm also handles `flex-shrink`, minimum content sizes, and multiple
resolution passes. This module treats a declared width as the whole
starting point, with no fallback to content size and no shrinking — real
enough to demonstrate the proportional-growth mechanism correctly, while
skipping the parts of the spec that would require wiring in Module 11 and
12's machinery for a comparatively small teaching payoff.

### `flex-direction` is always row (horizontal), never column

**(c) Our convention — explicit scope-out.** Column-direction flex swaps
which axis is "main" and reuses cross-axis alignment rules this module
doesn't implement at all. Restricting to row keeps `layout_flex_row`'s
single formula meaningful without a second, mirrored implementation for
column that this course's own test pages never need.

## Part B — Stacking

### Sort key is `(z_index, tree_order)`, z-index compared first

**(a) Forced by spec.** The CSS stacking-context painting order is
explicitly z-index-first: elements are grouped and painted by z-index
value, from most negative to most positive, and ONLY within an equal
z-index group does document order decide anything. A tuple sort key with
z-index in the first position and tree_order in the second is a direct,
structural expression of that priority — exactly the same pattern Module
9's cascade used for `(specificity, source_order)`.

### `z_index=None` ("auto") is treated identically to `z_index=0` for
    sorting purposes

**(c) Our convention — a named simplification of a real distinction.**
In real CSS, `z-index: auto` and `z-index: 0` behave identically for
PAINT ORDER (both sort as if z=0) but differently for whether the element
creates a brand-new stacking context of its own — a distinction that only
matters once nested z-index values inside that element are being
resolved relative to each other, which this module doesn't model at all
(every item here is treated as living in one single, flat stacking
context). Case B's test confirms the paint-order behavior this module
DOES implement; the stacking-context-creation distinction it does NOT
implement is named here rather than silently assumed away.

### `tree_order` is passed in explicitly, as a plain integer, rather than
    derived from walking a real tree inside this module

**(c) Our convention.** This module is deliberately decoupled from any
specific DOM/layout tree implementation — `paint_order()` only needs SOME
total ordering consistent with document order, not the tree itself. In a
full pipeline, `tree_order` would come from a single depth-first walk
(the same `walk()` pattern Module 8 already uses) assigning increasing
integers as it visits each node — a couple of lines, not shown here
because they'd duplicate logic Module 8 already established.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Extra space distributed proportionally to flex-grow | (a) forced by spec |
| 2 | flex-grow 0 never grows past basis, even with free space | (a) forced by spec (the real default) |
| 3 | Declared width stands in for flex-basis, no content sizing | (c) named simplification |
| 4 | Row direction only | (c) explicit scope-out |
| 5 | Sort key `(z_index, tree_order)`, z-index dominant | (a) forced by spec |
| 6 | `z_index=None` treated as `0` for paint order only | (c) named simplification (loses stacking-context creation) |
| 7 | `tree_order` passed in, not derived internally | (c) convention, decoupling |

## What We Proved

Two real, independently verified mechanisms: a three-item flex row with
grow ratios 1:2:1 distributed exactly 300px of free space as 75/150/75
— the center item's extra space was proven to be exactly double its
siblings', and total widths summed to exactly the 600px container; a
second flex row with all grow values at 0 (the default) proved items
do NOT stretch to fill unused space unless told to. Separately, a
5-item stacking test proved a negative z-index item painted first
despite being third in document order, two z-index-tied items with
z-index 0 (one explicit, one `auto`) were correctly ordered by document
position, and two z-index-2 items were likewise tied and ordered
correctly, ending up painted last — on top of everything. See
`tutorial.html` section 06 for the full, unedited output. This closes
Phase 3. Module 14 starts Phase 4: turning all of this now-complete
geometry into an actual list of things to draw.
