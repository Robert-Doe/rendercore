# DECISIONS.md — Module 12: Text Layout & Line Breaking

Source file: `text_layout.py`.

Category key: **(a)** forced by platform/spec · **(b)** forced by an
external contract · **(c)** our own convention.

---

### Greedy, first-fit line breaking — not a globally optimal algorithm

**(b) External contract — this is what browsers actually do.** There are
two well-known families of line-breaking algorithm: greedy/first-fit
(pack words onto the current line until one doesn't fit, then start a new
line — never reconsidering earlier decisions) and globally optimal
(Knuth-Plass, used by TeX and most word processors' "justify" mode, which
can revisit earlier line breaks to minimize total raggedness across the
whole paragraph). Real browsers use greedy line breaking for ordinary
text flow — it's cheaper (single pass, no backtracking) and matches what
CSS actually specifies for normal (non-justified) text. `wrap_words()`
implements greedy breaking specifically because that's the real,
spec-aligned behavior for the CSS this course builds, not because it's
simpler to implement (though it is).

### A word wider than `max_width` still gets placed on its own line,
    never split mid-word, never dropped, never causes an infinite loop

**(a) Forced by necessity.** If `wrap_words()` refused to place an
over-wide word until it "fit," it would loop forever — nothing about a
word's width changes between iterations. Placing it alone (`current`
being empty means the word is appended unconditionally, regardless of
its width) is the only choice that guarantees termination. This
also matches real CSS's default behavior (`overflow-wrap: normal`): a
long unbreakable token like a URL is allowed to overflow its container
rather than being silently truncated or breaking the layout algorithm.

### Text width measurement is a pluggable `measure_fn` callback, not a
    hardcoded formula inside the wrapping algorithm

**(c) Our convention — a deliberate separation of concerns.** Real
browsers separate "how wide is this text" (font metrics, a whole
subsystem involving the actual font file) from "given widths, where do
lines break" (the algorithm this module implements). Passing
`measure_fn` as a parameter means `wrap_words()` is fully testable and
fully correct RIGHT NOW, with zero dependency on Module 15's canvas or
any real font — and Module 15 can later supply a real
`tkinter.font.Font.measure` callable without `wrap_words()`'s own code
changing at all.

### `fixed_width_measure()` — every character is the same width

**(c) Our convention — an explicit, named simplification, not a claim
about how real text works.** Real fonts are virtually never monospaced
("i" is narrower than "m" in almost every font ever designed) — this
stand-in exists purely so this module's line-break math is exactly,
by-hand verifiable (every test case in this module was computed on paper
before running the code, and matched exactly). Module 15 replaces this
with real font metrics; nothing in `wrap_words()` needs to change for
that swap, precisely because of the `measure_fn` decision above.

### A space is treated as exactly one character wide (`space_width = char_width`)

**(c) Our convention — a consequence of the fixed-width simplification
above, not an independent choice.** In a monospaced stand-in, there's no
principled reason a space should measure differently from any other
character — real fonts do give the space glyph its own specific width,
which a real `measure_fn` (Module 15's) would report correctly without
this module's algorithm needing to know or care.

---

## Decisions We Made

| # | Decision | Category |
|---|----------|----------|
| 1 | Greedy first-fit line breaking, not globally optimal | (b) matches real browser behavior |
| 2 | Over-wide words placed alone rather than looping/splitting/dropping | (a) forced by termination guarantee |
| 3 | Width measurement is a pluggable callback | (c) convention, separation of concerns |
| 4 | Fixed-width (monospace) stand-in measurement for THIS module | (c) explicit, hand-verifiable simplification |
| 5 | Space treated as one character wide | (c) consequence of decision 4 |

## What We Proved

Three real, hand-verified cases: an 8-word sentence at a 100px width
wrapped into exactly the 5 lines predicted by hand arithmetic before the
code ever ran, each line positioned 20px below the last; a single
34-character word far wider than its 100px container was placed on its
own line — 340px wide, deliberately overflowing — without crashing,
looping, or corrupting the words around it; and the identical sentence,
given a 1000px container instead, correctly collapsed onto a single line,
proving the SAME algorithm adapts to different available widths rather
than having wrapping hardcoded. See `tutorial.html` section 06 for the
full, unedited output. This completes Phase 3 (Track 1's geometry phase);
Module 13 adds flexbox and z-index stacking, then Phase 4 turns all of
this geometry into actual pixels.
