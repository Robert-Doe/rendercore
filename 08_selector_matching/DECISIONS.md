# DECISIONS.md — Module 8: Selector Matching Engine

Source file: `selector_matching.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Matching proceeds right-to-left (rightmost compound against the node
    itself, then walking ancestors leftward)

**(b) External contract.** This is how real CSS selector matching is
actually defined and, more importantly, how it's efficiently
*implementable*: the rightmost compound (the "key selector") is checked
against the candidate node directly — an O(1)-ish check — before any
ancestor walking happens at all. Checking left-to-right would mean
starting from the document root and searching downward for a matching
path to the node for every single rule, against every node — dramatically
more work. Real browser engines match right-to-left specifically for this
performance reason; we adopt the same order both because it's correct and
because it's the reason real engines do it that way.

### Greedy nearest-ancestor matching, with no backtracking

**(a) Forced by a provable property of descendant-only combinator chains,
not a shortcut.** For a selector using only descendant combinators
(`a b c`), the ancestors of any node form a single, strictly linear chain
from that node up to the document root — never branching. Because
ancestry along one linear chain is transitive (if X is an ancestor of Y,
and Y is an ancestor of Z, then X is necessarily an ancestor of Z too),
picking the *nearest* ancestor that matches a given compound selector and
continuing the search from there can never eliminate a valid match that a
different (farther) ancestor choice would have found — any ancestor
satisfying a selector part further to the left is, by transitivity, also
an ancestor of the nearer match. This module's `_find_matching_ancestor`
takes advantage of exactly this fact to avoid backtracking. (This
guarantee stops holding once child, sibling, or `:has()`-style
combinators are mixed in — which Module 7 doesn't parse in the first
place, so the gap never surfaces here.)

### A compound selector's constraints (type, id, classes) are ANDed
    together, never ORed

**(b) External contract.** `div.card#hero` means "an element that is
simultaneously a `div`, AND has class `card`, AND has id `hero`" — not
"any element matching one of these three." `matches_simple()`'s three
early `return False` checks directly encode this AND relationship; there
is no valid alternative reading of a compound selector's meaning.

### `set(simple.classes).issubset(node_classes(node))`, not an exact match

**(a) Forced by spec.** A selector requiring class `card` matches an
element with `class="card featured"` just as much as one with
`class="card"` alone — a node can have additional classes beyond what a
given selector asks for. Using subset-containment rather than set
equality is the only correct implementation of "has (at least) these
classes."

### `matching_rules()` returns results in source order, not matched-rule order or any other order

**(c) Our convention, forward-looking.** Nothing in this module needs
source order — it's preserved here purely because Module 9's cascade
algorithm needs to break ties between equally-specific rules by which one
appeared later in the stylesheet, and that information only exists if
this module doesn't discard or reorder it. `matching_rules()` is written
as a simple list-comprehension filter specifically so the input list's
order passes through unchanged.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Matching proceeds right-to-left (key selector first) | (b) contract, also a real performance reason |
| 2 | Greedy nearest-ancestor matching, no backtracking | (a) provably correct for descendant-only combinators |
| 3 | Compound selector constraints are ANDed | (b) external contract |
| 4 | Class matching uses subset containment | (a) forced by spec |
| 5 | Matched rules returned in source order | (c) convention, needed by Module 9 |

## What We Proved

Matching four different real DOM nodes against a six-rule stylesheet
produced exactly the expected rule sets in every case: a class-bearing
link matched its class-specific selector plus its plainer ancestor
selector plus the universal rule (3 rules); a plain sibling link matched
everything except the class-specific one (2 rules); a `div` with both a
class and an id matched both of those selectors plus universal (3 rules);
and — the case that actually tests whether matching respects selector
structure rather than just "is this a descendant of something styled" — a
`<p>` nested inside that `div` matched only its own type selector plus
universal (2 rules), correctly NOT matching `.card` or `#hero`, because
neither of those selectors has a second compound that would reach into
descendants. See `tutorial.html` section 06 for the full, unedited
output. Module 9 takes these exact matched-rule lists and resolves them
down to one final value per CSS property per node.
