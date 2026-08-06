# DECISIONS.md — Module 11: Block & Inline Layout

Source file: `block_layout.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Block auto-width fills the containing block minus the box's own
    margin/border/padding

**(a) Forced by spec.** CSS defines that a block-level box in normal flow
with `width: auto` takes up all remaining horizontal space in its
containing block — this is precisely why block elements like `<div>`
visually "stack full-width" by default. `_resolve_size()`'s
`available - pad - bor` formula is this rule, and it's exactly the
resolution Module 10 explicitly deferred (see Module 10's DECISIONS.md) —
this module is where that promise gets kept.

### Auto height is computed AFTER laying out all children, from where the
    cursor ends up

**(a) Forced by spec, and forced by dependency order.** A block box with
`height: auto` is defined to size itself to fit its content — there's no
way to know that size without first knowing how tall the content actually
is. `layout_block()`'s loop lays out every child (recursively computing
each child's own full height, including any auto-height children of
THEIRS) before computing `content_height = cursor_y - content_y`. This
mirrors real layout engines' actual constraint: for block flow,
**position** is naturally top-down (a child needs its parent's resolved
position first) while **auto-size** is naturally bottom-up (a parent
needs its children's resolved sizes first) — and one recursive function
handles both directions correctly simply because of when each line of
code runs relative to the recursive call.

### `ContainingBlock.y` means "where THIS box's margin box starts," not
    "the parent's content top"

**(c) Our convention, chosen to keep the stacking loop simple.** Every
sibling gets a different `y` (the running cursor), while `x` and `width`
stay identical for every sibling with the same parent — because in a
block formatting context, siblings stack vertically but align
horizontally against the same containing block edges. Folding "the
cursor position for this specific box" into the same `ContainingBlock`
struct used for x/width, rather than a separate parameter, keeps
`layout_block`'s signature to one context object per call.

### Only `display: block` children are laid out; everything else is
    skipped entirely

**(c) Our convention — explicit scope-out, matching the roadmap's own
Module 11/12 split.** Real CSS block formatting contexts have rules for
wrapping runs of inline content into anonymous block boxes, which this
module doesn't implement — inline content and text wrapping are Module
12's entire job. A `Text` node, or an `Element` whose computed `display`
isn't `"block"`, is silently skipped by this module's child loop rather
than mishandled.

### No user-agent stylesheet — `display: block` must be stated explicitly
    in test CSS

**(c) Our convention — explicit scope-out.** Real browsers ship a
built-in stylesheet that makes `<div>`, `<p>`, `<body>`, etc. default to
`display: block` without the page's own CSS saying so — Module 9's
`INITIAL_VALUES` table defaults `display` to `"inline"` for everything,
matching plain CSS-spec defaults with no browser-specific overrides. This
module's own test CSS has to say `body, div { display: block; }`
explicitly as a result — a real, deliberate gap named here rather than
quietly patched by hardcoding tag names somewhere in the layout code.

### A real bug this module's own development run caught: shorthand `padding: 10px` silently produced zero padding

**(c) Noted because it happened, not as a hypothetical.** The first test
stylesheet for this module used `padding: 10px;` (CSS shorthand). Module
7's parser stores this literally as a declaration for the property named
`"padding"` — it does NOT expand shorthand into `padding-top`/`-right`/
`-bottom`/`-left` (a limitation already named in Module 9's DECISIONS.md).
`box_model.py`'s `_edges()` reads `padding-top` etc. specifically, never
sees a value for it, and silently defaults to `0` for every side —
producing a technically-not-crashing but completely wrong layout (a
420px-wide box came out reporting 400px, with the padding just missing).
Running the real layout output — not just reading the code — is what
surfaced this; the fix was rewriting the test CSS to use longhand
properties explicitly, which is also the correct workaround for any real
stylesheet used with this course's engine until a later extension adds
shorthand expansion to Module 7.

### A second bug this run caught: two of the demo's own assertions were
    wrong, not the layout code

**(c) Noted because it happened.** After fixing the padding gap, two
checks still printed `False`. Both turned out to be errors in the TEST's
own expected-value arithmetic, not the layout algorithm: one assertion
re-subtracted the parent's padding a second time when checking a child's
auto-width (double-counting something the child's containing block width
had already accounted for), and another compared two nodes' CONTENT-box y
coordinates to check vertical stacking distance, when the correct
comparison for "how far did the layout cursor move" is each node's
BORDER-box y coordinate (content y already bakes in that node's own
padding/border offset, which differs per node and isn't part of the
cursor-movement question being asked). Fixing the test's own math — not
the layout code, which was already correct — made both checks pass. Left
in as a reminder that a failing check can mean the code is wrong OR the
check is; both have to be considered.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Block auto-width fills containing block minus own edges | (a) forced by spec |
| 2 | Auto-height computed from children after they're laid out | (a) forced by spec + dependency order |
| 3 | `ContainingBlock.y` reused as the per-sibling stacking cursor | (c) convention |
| 4 | Only `display: block` children laid out; rest skipped | (c) explicit scope-out (Module 12's job) |
| 5 | No user-agent stylesheet; `display: block` must be explicit | (c) explicit scope-out |
| 6 | Shorthand `padding`/`margin` values silently ignored (real bug found) | (c) known gap, worked around with longhand CSS |

## What We Proved

A three-level-deep tree of block boxes — `body` containing `#outer`
containing `#a` and `#b`, `#b` itself containing `#b1` and `#b2` — laid
out with fully correct, hand-verified geometry: `#outer`'s explicit
400px width stayed 400px rather than stretching to the 800px viewport;
`#a`'s auto width correctly filled `#outer`'s content box exactly; `#b`'s
border box started exactly 70px below `#a`'s (50px height + 20px
margin-bottom, both real numbers from the stylesheet); `#b`'s auto height
correctly came out to 80px — the exact sum of `#b1` and `#b2`'s margin-box
heights, computed from those children before `#b`'s own box was finished;
and `#outer`'s own auto height correctly summed to 164px. Two real bugs
(a DOM-whitespace-node lookup error, and a CSS-shorthand gap) and two
flawed test assertions were caught by running this module and reading its
actual output, not by reading the code — see `tutorial.html` section 06
for the fully corrected, unedited final run. Module 12 now adds the piece
this module explicitly skips: text and inline content, laid out into
wrapped lines.
