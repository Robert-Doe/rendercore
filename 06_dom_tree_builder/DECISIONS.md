# DECISIONS.md — Module 6: HTML Tree Builder / DOM Construction

Source file: `dom_tree_builder.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### A synthetic `#document` root always at the bottom of the stack

**(c) Our convention.** Text or tags appearing before any real element
still need somewhere valid to attach — rather than special-casing "the
stack might be empty," the stack always starts with one root node that is
never popped (end-tag matching explicitly skips index 0; see the loop
`range(len(stack) - 1, 0, -1)`). This mirrors how a real DOM always has a
single `Document` node as the ultimate ancestor of everything, including
comments and the doctype.

### `VOID_ELEMENTS` are never pushed onto the open-elements stack

**(a) Forced by spec.** HTML defines `<br>`, `<img>`, `<input>`, and a
fixed list of others as having no content model at all — `<br>next text`
is not "a `<br>` containing 'next text'," it's a `<br>` followed by a
sibling text node. If the tree builder pushed these onto the stack like
any other element, every void element would incorrectly "swallow" all
following content as its children until some unrelated end tag happened
to pop it. Case 3's test exists specifically to catch a regression here.

### `AUTO_CLOSE_ON_TOP` only checks the immediate top of the stack, not
    an arbitrary ancestor

**(c) Our convention — a real, named simplification.** The actual HTML
parsing spec's "implied end tags" behavior is boundary-aware: a stray
`<li>` closes an open `<li>` even if other non-boundary elements are
technically between them, but stops looking once it hits a container
like `<ul>`/`<ol>`. Implementing that correctly means tracking which
elements count as boundaries for which auto-close rules — real complexity
that a from-scratch teaching module can reasonably skip. Checking only
the stack's top element handles the overwhelmingly common real-world case
(`<p>A<p>B`, `<li>A<li>B`) correctly, and is wrong only for HTML that
interposes an unrelated, non-boundary tag between two `<p>`s — a pattern
that's both rare and arguably bad HTML to begin with.

### An end tag closes everything from its match to the top of the stack
    (`del stack[match_idx:]`), not just its own match

**(a) Forced by tree-structure necessity, not a free choice.** If
`</b>` closes a `<b>` that has an unclosed `<i>` open inside it, the `<i>`
element cannot remain "open" afterward — its parent no longer exists on
the path from the root. Popping everything above the match, not just the
match itself, is the only way to keep the open-elements stack consistent
with the tree actually being built. This is also exactly what Case 5
exercises.

### The adoption agency algorithm is NOT implemented

**(c) Our convention — the most consequential scope-out in this module,
named explicitly because it changes real output.** Real browsers, on
seeing `<b>Bold <i>both</b> more</i>`, don't just close `<i>` when `</b>`
closes `<b>` — they run an algorithm (WHATWG HTML §13.2.6.4.7, informally
called the "adoption agency algorithm") that reopens a fresh `<i>` around
the content that follows, so "more" stays visually italic. This module's
simpler stack-popping approach closes `<i>` and does not reopen it — Case
5's own printed output shows " more" ending up as a plain sibling text
node of `<b>`, not re-wrapped. The recovery this module does implement
(auto-closing `<p>`/`<li>`, ignoring stray end tags, handling void
elements, correctly nesting despite EOF) is real and spec-aligned; this
one case is where it diverges, and it's called out rather than glossed
over.

### Stray end tags with no matching open element are silently ignored

**(a) Forced by spec.** WHATWG HTML explicitly defines this behavior:
an end tag token that doesn't match anything currently open is simply
discarded, not treated as an error that halts parsing. Real pages contain
this kind of markup constantly (often from buggy templating), and a
browser that stopped parsing on every stray end tag would be unusable.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Synthetic `#document` root, never popped | (c) convention |
| 2 | Void elements never pushed onto the stack | (a) forced by spec |
| 3 | Auto-close only checks stack top, not a boundary-aware ancestor scan | (c) named simplification |
| 4 | End tag closes match + everything above it | (a) forced by tree consistency |
| 5 | No adoption agency algorithm — misnested tags aren't reopened | (c) explicit, consequential scope-out |
| 6 | Unmatched end tags are silently ignored | (a) forced by spec |

## What We Proved

Five real, verified cases: an unclosed `<p>` correctly auto-closed by the
next `<p>` (siblings, not nesting); three unclosed `<li>` elements
correctly became siblings under one `<ul>`; a void `<br>` correctly did
not swallow the text after it; a tag left open all the way to end-of-input
still produced a correctly nested tree; and a misnested `<b>`/`<i>` pair
was handled with real (if simplified) recovery, with the exact point where
this module's behavior diverges from a real browser's demonstrated and
explained rather than hidden. See `tutorial.html` section 06 for the full,
unedited output of all five. Module 7 leaves HTML behind and starts
parsing CSS into a structured rule list.
