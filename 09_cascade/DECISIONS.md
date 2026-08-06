# DECISIONS.md — Module 9: The Cascade

Source file: `cascade.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Specificity represented as a 3-tuple `(ids, classes, types)`, compared
    with plain tuple comparison

**(a) Forced by spec, and forced by how Python tuples compare.** The CSS
specificity algorithm is explicitly defined as a positional comparison —
any number of id matches outweighs any number of class matches, which in
turn outweighs any number of type matches; you never "add up" across
categories into one number (100 classes never outweigh 1 id). Python's
built-in tuple comparison — compare element 0 first, only fall through to
element 1 on a tie, and so on — is not a convenient coincidence we're
exploiting; it is a structurally exact match for how the spec defines
specificity comparison, which is why `specificity()` returns a tuple
instead of a single weighted integer.

### `max(pool, key=lambda c: (c[0], c[1]))` as the entire tie-breaking rule

**(a) Forced by spec, and forced by how Python's `max` breaks ties.**
Composing the sort key as `(specificity, source_order_index)` means
specificity is compared first (always dominant), and `source_order_index`
only matters when specificity is exactly equal — at which point "the
declaration that appears later in the stylesheet wins" is exactly what
comparing plain increasing integers and taking the max produces. This is
not a clever trick; it's the direct spec rule ("last one wins" on a full
tie) expressed as the only thing left for the tuple's second element to
decide once the first element ties.

### `!important` declarations are considered as a completely separate
    pool, not just added weight to specificity

**(b) External contract.** The cascade spec treats "importance" as an
earlier, higher-priority sorting criterion than specificity — not a bonus
added to it. A `!important` declaration with LOW specificity still beats
a normal declaration with the HIGHEST possible specificity (an id
selector). `compute_style()` models this correctly as two disjoint pools
(`important_cands` vs. the rest), picking from the important pool
whenever it's non-empty, and falling through to the normal pool only when
it's empty — never letting normal-declaration specificity "outvote" an
important one. Case 3's test exists specifically to prove this: `#special`
has higher specificity than `.override`, and `.override` still wins,
because it's `!important`.

### Rule specificity is computed per matched selector within a comma
    group, taking the max

**(b) External contract.** `.a, .b.c { ... }` is really two independent
selectors sharing one declaration block, with two different specificities
(`0,1,0` and `0,2,0`). If an element matches via the `.b.c` half, that
half's higher specificity is what the spec says should apply to that
match — not the lower specificity of the OTHER selector in the group that
didn't even match this element. `max(specificity(s) for s in matched)`
implements exactly this.

### Inheritance is implemented as "copy from parent's ALREADY-COMPUTED
    style," which requires a strict top-down tree walk

**(a) Forced by dependency order, not a choice.** A child can only
inherit a value its parent has already resolved — computing a child's
style before its parent's would mean inheriting from nothing.
`compute_all()`'s `_walk()` explicitly computes the parent's style, then
recurses into children passing that finished style down — never the
reverse. This mirrors the same "parent before child" recursion order
required by layout (Modules 10–13) for exactly the same reason: a
child's answer depends on the parent's answer already existing.

### `INHERITED_PROPERTIES` and `INITIAL_VALUES` are small, explicitly
    incomplete tables

**(c) Our convention — explicit scope-out.** Real CSS defines an
inherited/not-inherited flag and a specific initial value for every
property in the spec (dozens of them). This module defines only the
handful (`color`, `font-*`, `line-height`, `text-align`; initial values
for `color`, `font-weight`, `font-size`, `display`) that this module's own
test cases exercise, named explicitly as a starting point rather than a
claim of completeness — later modules (10+) extend these tables as layout
needs more properties.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Specificity as a 3-tuple, compared positionally | (a) forced by spec + tuple semantics |
| 2 | Tie-break key `(specificity, source_order)` | (a) forced by spec's "last wins" rule |
| 3 | `!important` as a separate, higher-priority pool | (b) external contract |
| 4 | Per-matched-selector specificity, max across a comma group | (b) external contract |
| 5 | Strict top-down tree walk for inheritance | (a) forced by dependency order |
| 6 | Small, explicitly incomplete inherited/initial-value tables | (c) explicit scope-out |

## What We Proved

Six real, verified outcomes from one run: a class selector beat a type
selector declared later in the source (specificity outranks order); two
equally-specific class selectors resolved by which appeared later
(order only matters on a true tie); an `!important` declaration with
lower specificity beat a plain declaration with higher specificity
(importance outranks specificity entirely); a `<span>` with no color rule
of its own correctly inherited its parent's *computed* red, while a
non-inherited `border` property correctly did not leak down to it; and an
element with no matching rule for `font-weight` anywhere fell back
correctly to the initial value `normal`. See `tutorial.html` section 06
for the full, unedited output. This closes Phase 2 — every node in a real
tree now has one deterministic, fully-resolved computed style. Module 10
starts turning those computed styles into actual geometry.
